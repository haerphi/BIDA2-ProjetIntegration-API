from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework.exceptions import AuthenticationFailed

class HelloWorldView(APIView):
    """
    A simple View for testing the API. Returns a standard 'hello world' message.
    """
    def get(self, request):
        return Response({"hello": "world"})


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes JWT token retrieval by setting the username field to 'affiliation_number'.
    """
    username_field = 'affiliation_number'


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Extends TokenObtainPairView using CustomTokenObtainPairSerializer for custom login fields.
    """
    serializer_class = CustomTokenObtainPairSerializer


class GoogleLoginSerializer(serializers.Serializer):
    """
    Serializer to handle incoming Google ID token and validate it against Google's OAuth2 endpoints.
    """
    token = serializers.CharField(required=True, help_text="Google ID token")

    def validate(self, attrs):
        token = attrs.get('token')
        try:
            # Verify token via Google SDK using client id configured in settings
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID, clock_skew_in_seconds=10
            )
        except ValueError as e:
            raise serializers.ValidationError({"token": f"Invalid Google token. Details: {str(e)}"})

        email = idinfo.get('email')
        sub = idinfo.get('sub') # Google Subject ID
        
        if not sub:
            raise serializers.ValidationError({"token": "Token does not contain a subject ID."})

        User = get_user_model()
        
        # 1. Attempt to find the user by their Google Subject ID
        user = User.objects.filter(google_subject_id=sub).first()
        
        # 2. If not found, try to match by email (applicable on first login via Google)
        if not user:
            if not email:
                raise serializers.ValidationError({"token": "Token does not contain an email for first-time matching."})
            user = User.objects.filter(email=email).first()
            if user:
                # Link the user account to the Google account for subsequent logins
                user.google_subject_id = sub
                user.save()

        # Check if user exists after both lookup attempts
        if not user:
            raise AuthenticationFailed("No active account found with the given Google credentials. Please ask an administrator to register you.")

        # Ensure the user account is currently active
        if not user.is_active:
            raise AuthenticationFailed("This account is inactive.")

        attrs['user'] = user
        return attrs


class GoogleLoginView(APIView):
    """
    Authenticate a user with a Google ID token.
    If the email matches an existing user or subject id matches, return JWT access/refresh tokens.
    """
    permission_classes = [] # Public endpoint 

    @extend_schema(request=GoogleLoginSerializer, responses={200: dict, 401: dict, 400: dict})
    def post(self, request, *args, **kwargs):
        # Initialize GoogleLoginSerializer
        serializer = GoogleLoginSerializer(data=request.data)
        
        # Validate data or respond with bad request
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Generate refresh/access tokens for authenticated user
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })