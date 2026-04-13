from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.accounts.permissions import IsAdminRole
from members.models import Member
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationRequestSerializer
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

    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        court = self.get_object()
        serializer = ReservationRequestSerializer(data=request.data, context={'court': court})
        
        if serializer.is_valid():
            creator = request.user.profile
            members_ids = serializer.validated_data['members']
            
            reservation = Reservation.objects.create(
                court=court,
                creator=creator,
                date_time=serializer.validated_data['date_time'],
                duration=serializer.validated_data['duration']
            )
            
            players_to_add = Member.objects.filter(id__in=members_ids)
            reservation.players.add(*players_to_add)
            if creator not in players_to_add:
                reservation.players.add(creator)
                
            return Response({
                'reservation_id': reservation.id,
                'court_id': court.id,
                'date_time': reservation.date_time,
                'duration': reservation.duration
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='book')
    def cancel(self, request, pk=None):
        reservation = self.get_object()
        reservation.delete()
        return Response({'status': 'Reservation cancelled successfully'}, status=status.HTTP_200_OK)
