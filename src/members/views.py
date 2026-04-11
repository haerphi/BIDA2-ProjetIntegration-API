from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.accounts.permissions import IsAdminRole
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import MemberProfile
from .serializers import (
    MemberProfileSerializer, 
    MemberProfileCreateSerializer, 
    PasswordUpdateSerializer
)

class MemberProfileViewSet(viewsets.GenericViewSet):
    queryset = MemberProfile.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = [
        'ranking', 'gender', 'is_active', 'affiliation_number', 
        'email', 'firstname', 'lastname', 'postal_code', 
        'country', 'phone', 'birth_date', 'role'
    ]
    ordering_fields = ['lastname', 'ranking', 'firstname', 'created_at', 'role']

    def get_serializer_class(self):
        if self.action == 'create':
            return MemberProfileCreateSerializer
        elif self.action in ['set_password', 'me_set_password']:
            return PasswordUpdateSerializer
        return MemberProfileSerializer

    def get_permissions(self):
        admin_actions = ['create', 'update', 'partial_update', 'destroy', 'set_password']
        if self.action in admin_actions:
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    # --- Actions standards ---

    def list(self, request):
        """ Route: GET /api/members/ """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """ Route: GET /api/members/<id>/ """
        member = self.get_object() 
        serializer = self.get_serializer(member)
        return Response(serializer.data)

    def create(self, request):
        """ Route: POST /api/members/ """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """ Route: PUT /api/members/<id>/ """
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """ Route: PATCH /api/members/<id>/ """
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """ Route: DELETE /api/members/<id>/ """
        member = self.get_object()
        if member.user:
            member.user.delete()
        else:
            member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- Actions "Custom" ---

    @action(detail=True, methods=['patch'])
    def set_password(self, request, pk=None):
        """ Route: PATCH /api/members/<id>/set_password/ """
        member = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.user.set_password(serializer.validated_data['password'])
            member.user.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """ Route: GET /api/members/me/ (Logged-in member profile) """
        try:
            member = request.user.profile
        except getattr(MemberProfile, 'DoesNotExist', Exception):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(member)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='me')
    def me_update(self, request):
        """ Route: PUT /api/members/me/ (Logged-in member profile update) """
        try:
            member = request.user.profile
        except getattr(MemberProfile, 'DoesNotExist', Exception):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'], url_path='me')
    def me_delete(self, request):
        """ Route: DELETE /api/members/me/ (Logged-in member profile deletion) """
        try:
            member = request.user.profile
        except getattr(MemberProfile, 'DoesNotExist', Exception):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if member.user:
            member.user.delete() # Deleting the User also deletes the MemberProfile by cascade
        else:
            member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['patch'], url_path='me/set_password')
    def me_set_password(self, request):
        """ Route: PATCH /api/members/me/set_password/ """
        try:
            member = request.user.profile
        except getattr(MemberProfile, 'DoesNotExist', Exception):
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.user.set_password(serializer.validated_data['password'])
            member.user.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)