from rest_framework import serializers
from .models import Court

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'number']
