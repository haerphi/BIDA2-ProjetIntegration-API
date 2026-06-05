from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.accounts.permissions import IsAdminRole
from members.models import Member
from .models import Court, Reservation
from .serializers import CourtSerializer, ReservationRequestSerializer, ReservationSerializer
from .utils import check_player_reservation_limits

class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.filter(is_active=True).order_by('name')
    serializer_class = CourtSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], pagination_class=None)
    def all(self, request):
        courts = self.get_queryset()
        serializer = self.get_serializer(courts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def reservations(self, request):
        reservations = Reservation.objects.all().select_related('creator').order_by('date_time')
        serializer = ReservationSerializer(reservations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-weekly-reservations')
    def my_weekly_reservations(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'date query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            parsed_dt = parse_datetime(date_str)
            if parsed_dt:
                if timezone.is_naive(parsed_dt):
                    parsed_dt = timezone.make_aware(parsed_dt)
                target_date = parsed_dt
            else:
                parsed_d = parse_date(date_str)
                if not parsed_d:
                    raise ValueError
                target_date = timezone.make_aware(datetime.combine(parsed_d, datetime.min.time()))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date format. Expected YYYY-MM-DD or ISO 8601 datetime.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # week starts Sunday — mirrors check_player_reservation_limits
        offset = (target_date.weekday() + 1) % 7
        start_of_week = target_date.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=offset)
        end_of_week = start_of_week + timedelta(days=7)

        reservations = Reservation.objects.filter(
            Q(creator=request.user) | Q(players=request.user),
            date_time__gte=start_of_week,
            date_time__lt=end_of_week
        ).distinct().select_related('creator').order_by('date_time')

        serializer = ReservationSerializer(reservations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='check-eligibility')
    def check_eligibility(self, request):
        date_time_str = request.query_params.get('date_time')
        if not date_time_str:
            return Response(
                {'error': 'date_time query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            date_time = parse_datetime(date_time_str)
            if not date_time:
                raise ValueError
            if timezone.is_naive(date_time):
                date_time = timezone.make_aware(date_time)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid date_time format. Expected ISO 8601.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        member_id = request.query_params.get('member_id')
        if member_id:
            try:
                user = Member.objects.get(id=member_id)
            except Member.DoesNotExist:
                return Response(
                    {'error': 'Member not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            user = request.user

        is_eligible, error_message = check_player_reservation_limits(user, date_time)

        return Response({
            'can_book': is_eligible,
            'reason': error_message
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'], url_path='reservations')
    def reservations_detail(self, request, pk=None):
        if request.method == 'GET':
            court = self.get_object()
            reservations = Reservation.objects.filter(court=court).select_related('creator').prefetch_related('players').order_by('date_time')

            date_str = request.query_params.get('date')
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    reservations = reservations.filter(date_time__date=date_str)
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Expected YYYY-MM-DD.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            serializer = ReservationSerializer(reservations, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            court = self.get_object()
            serializer = ReservationRequestSerializer(data=request.data, context={'court': court, 'request': request})

            if serializer.is_valid():
                creator = serializer.validated_data['creator']
                members_ids = serializer.validated_data['members']

                reservation = Reservation.objects.create(
                    court=court,
                    creator=creator,
                    date_time=serializer.validated_data['date_time'],
                    duration=serializer.validated_data['duration'],
                    type=serializer.validated_data['type'],
                    comment=serializer.validated_data.get('comment')
                )

                players_to_add = Member.objects.filter(id__in=members_ids)
                reservation.players.add(*players_to_add)

                if creator not in players_to_add:
                    reservation.players.add(creator)

                return Response({
                    'reservation_id': reservation.id,
                    'court_id': court.id,
                    'date_time': reservation.date_time,
                    'duration': reservation.duration,
                    'type': reservation.type,
                    'comment': reservation.comment
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path=r'reservations/(?P<reservation_id>[^/.]+)')
    def cancel_reservation(self, request, pk=None, reservation_id=None):
        reservation = get_object_or_404(Reservation, pk=reservation_id)

        # Only the creator or an admin can cancel
        is_admin = request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='admin').exists()
        if reservation.creator != request.user and not is_admin:
            return Response(
                {'error': 'You are not allowed to cancel this reservation.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Enforce 24-hour cancellation window (datetime-precise)
        time_until = reservation.date_time - timezone.now()
        if time_until.total_seconds() < 86400:
            return Response(
                {'error': 'Reservations can only be cancelled at least 24 hours before the start time.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.delete()
        return Response({'status': 'Reservation cancelled successfully.'}, status=status.HTTP_200_OK)