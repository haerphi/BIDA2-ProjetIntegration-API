from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from .models import Court, Reservation
from members.models import MemberProfile

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'number']

class ReservationRequestSerializer(serializers.Serializer):
    members = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False
    )
    date_time = serializers.DateTimeField()
    duration = serializers.IntegerField()

    def validate_duration(self, value):
        if value not in [60, 120]:
            raise serializers.ValidationError("Duration must be 60 or 120 minutes.")
        return value

    def validate_members(self, value):
        if len(value) not in [1, 3]:
            raise serializers.ValidationError("The members array must contain exactly 1 or 3 members.")
        
        existing_members = MemberProfile.objects.filter(id__in=value).count()
        if existing_members != len(value):
            raise serializers.ValidationError("One or more member IDs provided are invalid or do not exist.")
            
        return value

    def validate_date_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("You cannot book a court in the past.")
        return value

    def validate(self, data):
        court = self.context['court']
        start_time = data['date_time']
        end_time = start_time + timedelta(minutes=data['duration'])

        window_start = start_time - timedelta(minutes=120)
        window_end = end_time + timedelta(minutes=120)
        
        overlapping_candidates = Reservation.objects.filter(
            court=court,
            date_time__gte=window_start,
            date_time__lte=window_end
        )
        
        for res in overlapping_candidates:
            res_start = res.date_time
            res_end = res_start + timedelta(minutes=res.duration)
            # Two intervals [start1, end1) and [start2, end2) overlap if:
            # start1 < end2 and start2 < end1
            if start_time < res_end and res_start < end_time:
                raise serializers.ValidationError({"date_time": "This court is already booked during the requested time."})

        return data
