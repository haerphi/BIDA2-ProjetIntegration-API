from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: dict}, description="Health check endpoint to verify the API is running.")
    def get(self, request):
        return Response({"status": "running"})
