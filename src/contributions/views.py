import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.http import HttpResponse
from .models import Contribution

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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
                success_url=f"{settings.FRONTEND_URL}/payment/success",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
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
            client_reference_id = session.get('client_reference_id')
            
            if client_reference_id:
                try:
                    contribution = Contribution.objects.get(id=client_reference_id)
                    contribution.status = 'completed'
                    contribution.save()
                except Contribution.DoesNotExist:
                    print(f"Contribution heavily misplaced: ID {client_reference_id} missing")

        return HttpResponse(status=200)

class ContributionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return Response({
            "has_paid": request.user.has_paid_contribution()
        }, status=status.HTTP_200_OK)
