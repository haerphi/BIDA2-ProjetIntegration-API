from django.core import paginator
from rest_framework.permissions import IsAdminUser
import stripe
from django.conf import settings
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.http import HttpResponse
from .models import Contribution


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Prevent double payments for the current year
        if request.user.has_paid_contribution():
            return Response(
                {'error': 'You have already paid your contribution for this year.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            # Create a pending contribution record
            contribution = Contribution.objects.create(
                member=request.user,
                amount=settings.CONTRIBUTION_AMOUNT_EUR,
                status='pending'
            )

            # Create a Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'bancontact', 'ideal'], # Common European methods
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'unit_amount': int(settings.CONTRIBUTION_AMOUNT_EUR * 100), # Amount in cents
                            'product_data': {
                                'name': 'Annual Club Contribution',
                                'description': f'Contribution for member {request.user.first_name} {request.user.last_name}',
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/contribution/success",
                cancel_url=f"{settings.FRONTEND_URL}/contribution/cancel",
                client_reference_id=str(contribution.id),
                customer_email=request.user.email,
            )

            # Save the session ID to the contribution
            contribution.stripe_session_id = checkout_session.id
            contribution.save()

            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        # Handle the checkout.session.completed event
        if event['type'] == 'checkout.session.completed':   
            session = event['data']['object']
            
            # Check if the payment was successful. For Stripe objects, use dot notation or bracket notation, not .get()
            payment_status = getattr(session, 'payment_status', None)
            
            if payment_status == 'paid':
                session_id = getattr(session, 'id', None)

                if session_id:
                    try:
                        contribution = Contribution.objects.get(stripe_session_id=session_id)
                        contribution.status = 'completed'
                        contribution.save()
                    except Contribution.DoesNotExist:
                        # TODO put this in a logger: this exception should not happen
                        print(f"Contribution with session ID {session_id} not found. :(")
                        pass
                    
            else:
                session_id = getattr(session, 'id', None)
                print(f"Checkout session {session_id} completed but payment_status is {payment_status}")

        return HttpResponse(status=200)

class ContributionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({
            "has_paid": request.user.has_paid_contribution()
        }, status=status.HTTP_200_OK)

class ContributionAmountView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get(self, request, *args, **kwargs):
        return Response({
            "amount": settings.CONTRIBUTION_AMOUNT_EUR
        }, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        new_amount = request.data.get('amount')
        if not new_amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_amount = float(new_amount)
        except ValueError:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        if new_amount < 0:
            return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
        settings.CONTRIBUTION_AMOUNT_EUR = new_amount
        return Response({'amount': settings.CONTRIBUTION_AMOUNT_EUR}, status=status.HTTP_200_OK)

class ContributionHistoryView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        first_name = request.query_params.get('first_name', None)
        last_name = request.query_params.get('last_name', None)
        email = request.query_params.get('email', None)
        year = request.query_params.get('year', None)
        contribution_status = request.query_params.get('status', None)

        # Validate pagination params
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except (TypeError, ValueError):
            page = 1
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit < 1:
                limit = 10
        except (TypeError, ValueError):
            limit = 10

        # Build query dynamically
        query = Q()
        if first_name:
            query &= Q(member__first_name__icontains=first_name.strip()) 
        if last_name:
            query &= Q(member__last_name__icontains=last_name.strip()) 
        if email:
            query &= Q(member__email__icontains=email.strip()) 
        
        if year:
            year_val = str(year).strip()
            if year_val.isdigit():
                query &= Q(created_at__year=year_val) 
        
        if contribution_status:
            status_val = str(contribution_status).strip().lower()
            if status_val == 'cancelled':
                status_val = 'failed'
            if status_val and status_val != 'all':
                query &= Q(status=status_val)

        all_contributions = Contribution.objects.filter(query).select_related('member').order_by('-created_at')
        paginator_instance = paginator.Paginator(all_contributions, limit)
        page_obj = paginator_instance.get_page(page)

        # serialize the contributions
        contributions_serialized = []
        for contribution in page_obj:
            contributions_serialized.append({
                'id': contribution.id,
                'member_id': contribution.member_id,
                'first_name': contribution.member.first_name,
                'last_name': contribution.member.last_name,
                'email': contribution.member.email,
                'amount': contribution.amount,
                'status': contribution.status,
                'created_at': contribution.created_at,
                'updated_at': contribution.updated_at
            })
        return Response({
            "data": contributions_serialized,
            "limit": paginator_instance.per_page,
            "total": paginator_instance.count,
            "page": page_obj.number,
            "total_pages": paginator_instance.num_pages
        }, status=status.HTTP_200_OK)


class MemberContributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, member_id=None, *args, **kwargs):
        if member_id:
            # If member_id is provided, check if the requester is an admin
            if not request.user.is_staff:
                return Response(
                    {"error": "You must be an admin to view other members' contributions."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            target_member_id = member_id
        else:
            # If no member_id, use the current user
            target_member_id = request.user.id

        q_status = request.query_params.get('status', None)
        q_year = request.query_params.get('year', None)

        # Validate pagination params
        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                page = 1
        except (TypeError, ValueError):
            page = 1
        try:
            limit = int(request.query_params.get('limit', 10))
            if limit < 1:
                limit = 10
        except (TypeError, ValueError):
            limit = 10

        query = Q(member_id=target_member_id)
        if q_status:
            status_val = str(q_status).strip().lower()
            if status_val == 'cancelled':
                status_val = 'failed'
            if status_val and status_val != 'all':
                query &= Q(status=status_val)
        
        if q_year:
            year_val = str(q_year).strip()
            if year_val.isdigit():
                query &= Q(created_at__year=year_val)

        contributions = Contribution.objects.filter(query).order_by('-created_at')
        
        paginator_instance = paginator.Paginator(contributions, limit)
        page_obj = paginator_instance.get_page(page)

        # Serialize the contributions
        contributions_serialized = []
        for contribution in page_obj:
            contributions_serialized.append({
                'id': contribution.id,
                'member_id': contribution.member_id,
                'amount': contribution.amount,
                'status': contribution.status,
                'created_at': contribution.created_at,
                'updated_at': contribution.updated_at
            })
            
        return Response({
            "data": contributions_serialized,
            "limit": paginator_instance.per_page,
            "total": paginator_instance.count,
            "page": page_obj.number,
            "total_pages": paginator_instance.num_pages
        }, status=status.HTTP_200_OK)