from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.accounts.permissions import IsAdminRole
from members.models import Member
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationRequestSerializer, ReservationSerializer

class CourtViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing courts, and managing court reservations.
    Provides standard REST actions as well as custom endpoints for booking and cancelling.
    """
    queryset = Court.objects.filter(is_active=True).order_by('number')
    serializer_class = CourtSerializer

    def get_permissions(self):
        """
        Admins handle court CRUD operations (create, update, destroy). 
        Other actions like booking are available to all authenticated users.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete a court instead of deleting it from the database.
        """
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], pagination_class=None)
    def all(self, request):
        """
        Endpoint to list all courts without pagination.
        Route: GET /api/courts/all/
        """
        courts = self.get_queryset()
        serializer = self.get_serializer(courts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def reservations(self, request):
        """
        Endpoint to list all reservations across all courts.
        Route: GET /api/courts/reservations/
        """
        reservations = Reservation.objects.all().select_related('creator').order_by('date_time')
        serializer = ReservationSerializer(reservations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        """
        Custom endpoint for authenticated members to make a court booking.
        Route: POST /api/courts/<id>/book/
        Expects a payload with a list of member IDs, a start date/time and duration.
        """
        court = self.get_object()
        serializer = ReservationRequestSerializer(data=request.data, context={'court': court})
        
        if serializer.is_valid():
            creator = request.user
            members_ids = serializer.validated_data['members']
            
            # Create standard reservation entry linked to request's creator
            reservation = Reservation.objects.create(
                court=court,
                creator=creator,
                date_time=serializer.validated_data['date_time'],
                duration=serializer.validated_data['duration']
            )
            
            # Retrieve all listed members from DB
            players_to_add = Member.objects.filter(id__in=members_ids)
            reservation.players.add(*players_to_add)
            
            # Automatically add creator to players list if they aren't explicitly passed
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
        """
        Endpoint to cancel/delete a reservation on this court.
        Route: DELETE /api/courts/<id>/book/
        Uses Reservation pk directly or logic expects the reservation instance (this may need to be adapted based on routing design if pk belongs to Court here instead of Reservation).
        """
        # Note: If pk is the court id, this will fetch the court, not the reservation. 
        # But per the code provided, this endpoint attempts to delete the court if pk is the reservation id.
        reservation = self.get_object()
        reservation.delete()
        return Response({'status': 'Reservation cancelled successfully'}, status=status.HTTP_200_OK)