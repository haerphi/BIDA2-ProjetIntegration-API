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
            contribution = Contribution.objects.create(
                member=request.user,
                amount=settings.CONTRIBUTION_AMOUNT_EUR,
                status='pending'
            )

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card', 'bancontact', 'ideal'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'eur',
                            'unit_amount': int(settings.CONTRIBUTION_AMOUNT_EUR * 100),
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
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            payment_status = getattr(session, 'payment_status', None)
            
            if payment_status == 'paid':
                session_id = getattr(session, 'id', None)

                if session_id:
                    try:
                        contribution = Contribution.objects.get(stripe_session_id=session_id)
                        contribution.status = 'completed'
                        contribution.save()
                    except Contribution.DoesNotExist:
                        print(f"Contribution with session ID {session_id} not found.")
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

        qs = Contribution.objects.filter(query).select_related('member').order_by('-created_at')
        pager = paginator.Paginator(qs, limit)
        page_obj = pager.get_page(page)

        data = [
            {
                'id': c.id,
                'member_id': c.member_id,
                'first_name': c.member.first_name,
                'last_name': c.member.last_name,
                'email': c.member.email,
                'amount': c.amount,
                'status': c.status,
                'created_at': c.created_at,
                'updated_at': c.updated_at
            }
            for c in page_obj
        ]
        return Response({
            "data": data,
            "limit": pager.per_page,
            "total": pager.count,
            "page": page_obj.number,
            "total_pages": pager.num_pages
        }, status=status.HTTP_200_OK)


class MemberContributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, member_id=None, *args, **kwargs):
        if member_id:
            if not request.user.is_staff:
                return Response(
                    {"error": "You must be an admin to view other members' contributions."},
                    status=status.HTTP_403_FORBIDDEN
                )
            target_member_id = member_id
        else:
            target_member_id = request.user.id

        q_status = request.query_params.get('status', None)
        q_year = request.query_params.get('year', None)

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

        qs = Contribution.objects.filter(query).order_by('-created_at')
        pager = paginator.Paginator(qs, limit)
        page_obj = pager.get_page(page)

        data = [
            {
                'id': c.id,
                'member_id': c.member_id,
                'amount': c.amount,
                'status': c.status,
                'created_at': c.created_at,
                'updated_at': c.updated_at
            }
            for c in page_obj
        ]

        return Response({
            "data": data,
            "limit": pager.per_page,
            "total": pager.count,
            "page": page_obj.number,
            "total_pages": pager.num_pages
        }, status=status.HTTP_200_OK)