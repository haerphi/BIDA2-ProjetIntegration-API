from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Court, Reservation
from members.models import Member

class CourtSerializer(serializers.ModelSerializer):
    """
    Standard ModelSerializer for returning Court information.
    """
    class Meta:
        model = Court
        fields = ['id', 'number']

class ReservationRequestSerializer(serializers.Serializer):
    """
    Serializer handling incoming booking requests and checking for rule violations 
    or scheduling conflicts before a Reservation object is created.
    """
    # Requires an array of member IDs
    members = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    date_time = serializers.DateTimeField()
    duration = serializers.IntegerField()

    def validate_duration(self, value):
        """
        Ensure court booking durations fit within approved slots (60 or 120 mins)
        """
        if value not in [60, 120]:
            raise serializers.ValidationError("Duration must be 60 or 120 minutes.")
        return value

    def validate_members(self, value):
        """
        Ensure player count matches expected ranges (usually for singles or doubles).
        Checks if the provided member ids actually exist in the database.
        """
        # Restrict standard play combinations
        if len(value) not in [1, 3]:
            raise serializers.ValidationError("The members array must contain exactly 1 or 3 members.")
        
        # Verify valid inputs against member roster
        existing_members = Member.objects.filter(id__in=value).count()
        if existing_members != len(value):
            raise serializers.ValidationError("One or more member IDs provided are invalid or do not exist.")
            
        return value

    def validate_date_time(self, value):
        """
        Prevent users from booking courts in the past.
        """
        if value < timezone.now():
            raise serializers.ValidationError("You cannot book a court in the past.")
        return value

    def validate(self, data):
        """
        Main complex validation comparing requested slot against existing bookings 
        on the selected court to prevent overlapping.
        """
        # Extract related court from context map
        court = self.context['court']
        
        # Determine exact start and end intervals
        start_time = data['date_time']
        end_time = start_time + timedelta(minutes=data['duration'])

        # Expand time window boundaries specifically to catch overlap intersections nearby 
        # (reduces database records processed vs a full table scan)
        window_start = start_time - timedelta(minutes=120)
        window_end = end_time + timedelta(minutes=120)
        
        overlapping_candidates = Reservation.objects.filter(
            court=court,
            date_time__gte=window_start,
            date_time__lte=window_end
        )
        
        # Manual overlap check using formula: start1 < end2 and start2 < end1
        for res in overlapping_candidates:
            res_start = res.date_time
            res_end = res_start + timedelta(minutes=res.duration)
            
            # If start1 < end2 and start2 < end1, then the blocks intersect
            if start_time < res_end and res_start < end_time:
                raise serializers.ValidationError({"date_time": "This court is already booked during the requested time."})

        return data