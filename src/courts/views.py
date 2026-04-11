from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.accounts.permissions import IsAdminRole
from .models import Court
from .serializers import CourtSerializer

class CourtViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing courts.
    """
    queryset = Court.objects.all().order_by('number')
    serializer_class = CourtSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]
