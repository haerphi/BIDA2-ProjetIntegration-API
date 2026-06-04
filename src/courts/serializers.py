from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Court, Reservation
from members.models import Member
from members.serializers import MemberSerializer

class CourtSerializer(serializers.ModelSerializer):
    """
    Standard ModelSerializer for returning Court information.
    """
    class Meta:
        model = Court
        fields = ['id', 'name']

class ReservationSerializer(serializers.ModelSerializer):
    """
    Serializer for listing reservations, providing information about who made it.
    """
    creator = MemberSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'court', 'date_time', 'duration', 'creator', 'type', 'comment']

class ReservationRequestSerializer(serializers.Serializer):
    """
    Serializer handling incoming booking requests and checking for rule violations 
    or scheduling conflicts before a Reservation object is created.
    """
    type = serializers.ChoiceField(choices=['simple', 'double', 'blocage_admin'])
    members = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    date_time = serializers.DateTimeField()
    duration = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_date_time(self, value):
        """
        Prevent users from booking courts in the past.
        """
        res_type = self.initial_data.get('type')
        if value < timezone.now() and res_type != 'blocage_admin':
            raise serializers.ValidationError("You cannot book a court in the past.")
        return value

    def validate(self, data):
        """
        Main complex validation comparing requested slot against existing bookings 
        on the selected court to prevent overlapping.
        Also validates duration and members count depending on the reservation type.
        """
        res_type = data.get('type')
        duration = data.get('duration')
        members = data.get('members', [])

        # If the reservation is not an admin blockage, ignore/clear the comment
        if res_type != 'blocage_admin':
            data['comment'] = None

        # Validate duration and members based on type
        if res_type == 'simple':
            if duration != 60:
                raise serializers.ValidationError({"duration": "Simple reservation must be exactly 60 minutes (1h)."})
            if len(members) != 1:
                raise serializers.ValidationError({"members": "Simple reservation must have exactly 1 member (+ the creator)."})
        elif res_type == 'double':
            if duration != 120:
                raise serializers.ValidationError({"duration": "Double reservation must be exactly 120 minutes (2h)."})
            if len(members) != 3:
                raise serializers.ValidationError({"members": "Double reservation must have exactly 3 members (+ the creator)."})
        elif res_type == 'blocage_admin':
            # The blocage_admin should only be for "admin" or "staff" or django group that has the permission
            request = self.context.get('request')
            if request and hasattr(request, 'user'):
                user = request.user
                is_admin = user.is_superuser or user.is_staff or user.groups.filter(name='admin').exists()
                if not is_admin:
                    raise serializers.ValidationError({"type": "Only admins, staff, or members of the admin group can create a blocage_admin reservation."})

        # Verify valid inputs against member roster if any members are provided
        if members:
            existing_members = Member.objects.filter(id__in=members).count()
            if existing_members != len(members):
                raise serializers.ValidationError({"members": "One or more member IDs provided are invalid or do not exist."})

            request = self.context.get('request')
            creator = request.user if request else None
            
            # Retrieve player objects
            players = list(Member.objects.filter(id__in=members))
            if creator and creator not in players:
                players.append(creator)

            # Check weekly reservation limits for all players
            from .utils import check_player_reservation_limits
            date_time = data.get('date_time')
            for player in players:
                is_eligible, error_message = check_player_reservation_limits(player, date_time)
                if not is_eligible:
                    raise serializers.ValidationError({"members": error_message})

        # Extract related court from context map
        court = self.context['court']
        
        # Determine exact start and end intervals and check for overlaps
        start_time = data['date_time']
        end_time = start_time + timedelta(minutes=duration)
        
        overlapping_candidates = Reservation.objects.filter(
            court=court,
            date_time__lt=end_time,
            date_time__gte=start_time - timedelta(days=30)
        )
        for candidate in overlapping_candidates:
            candidate_end_time = candidate.date_time + timedelta(minutes=candidate.duration)
            if start_time < candidate_end_time:
                raise serializers.ValidationError({
                    "date_time": "This court is already booked during the requested time slot."
                })

        return data