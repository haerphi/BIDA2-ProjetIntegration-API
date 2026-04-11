from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MemberProfile


class MemberProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberProfile
        fields = [
            'id', 'user', 'firstname', 'lastname', 'email', 'street', 'city',
            'postal_code', 'country', 'phone', 'birth_date', 'gender',
            'affiliation_number', 'ranking', 'is_active', 'role', 'created_at'
        ]
        read_only_fields = ['user', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')

        is_admin = False
        if request and request.user.is_authenticated:
            profile = getattr(request.user, 'profile', None)
            if profile and profile.role == 'admin':
                is_admin = True

        if request and hasattr(request, 'user') and request.user == instance.user:
            is_admin = True

        if not is_admin:
            representation.pop('email', None)

        return representation

    def update(self, instance, validated_data):
        if 'email' in validated_data and instance.user:
            instance.user.email = validated_data['email']
            instance.user.username = validated_data['email']
            instance.user.save()

        instance = super().update(instance, validated_data)

        return instance


class MemberProfileCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = MemberProfile
        fields = [
            'id', 'user', 'firstname', 'lastname', 'email', 'street', 'city',
            'postal_code', 'country', 'phone', 'birth_date', 'gender',
            'affiliation_number', 'ranking', 'is_active', 'role', 'created_at', 'password'
        ]
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data.get('email')

        user = User.objects.create_user(username=email, email=email, password=password)
        validated_data['user'] = user

        return super().create(validated_data)


class PasswordUpdateSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
