from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from core.accounts.permissions import IsAdminRole
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Member
from .serializers import (
    MemberSerializer, 
    MemberCreateSerializer, 
    PasswordUpdateSerializer
)

class MemberViewSet(viewsets.GenericViewSet):
    """
    Provides REST API views for viewing and interacting with Members.
    Includes custom endpoints to handle password reset, profile view/edit.
    """
    queryset = Member.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    # Filterable and sortable fields
    filterset_fields = [
        'ranking', 'gender', 'is_active', 'affiliation_number', 
        'email', 'first_name', 'last_name', 'postal_code', 
        'country', 'phone', 'birth_date'
    ]
    ordering_fields = ['last_name', 'ranking', 'first_name', 'created_at']

    def get_serializer_class(self):
        """
        Dynamically determine serializer based on the current action being performed.
        """
        if self.action == 'create':
            return MemberCreateSerializer
        elif self.action in ['set_password', 'me_set_password']:
            return PasswordUpdateSerializer
        return MemberSerializer

    def get_permissions(self):
        """
        Determine permissions dynamically. Admin role required for structural operations.
        Otherwise standard IsAuthenticated permission is enforced.
        """
        admin_actions = ['create', 'update', 'partial_update', 'destroy', 'set_password']
        if self.action in admin_actions:
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    # --- Standard REST Actions ---

    def list(self, request):
        """ 
        Retrieve a list of Members with optional filtering and ordering parameters.
        Route: GET /api/members/ 
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """ 
        Retrieve the details of a specific Member by primary key.
        Route: GET /api/members/<id>/ 
        """
        member = self.get_object() 
        serializer = self.get_serializer(member)
        return Response(serializer.data)

    def create(self, request):
        """ 
        Create a new Member account using the provided data payload.
        Route: POST /api/members/ 
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """ 
        Completely update a specific Member instance by replacing its details.
        Route: PUT /api/members/<id>/ 
        """
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """ 
        Partially update specific fields on a Member account.
        Route: PATCH /api/members/<id>/ 
        """
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """ 
        Delete a specific Member instance by ID.
        Route: DELETE /api/members/<id>/ 
        """
        member = self.get_object()
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- Custom Endpoints ---

    @action(detail=True, methods=['patch'])
    def set_password(self, request, pk=None):
        """ 
        Update the password of a specific member account. Primarily for administrative use.
        Route: PATCH /api/members/<id>/set_password/ 
        """
        member = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.set_password(serializer.validated_data['password'])
            member.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put', 'patch', 'delete'])
    def me(self, request):
        """ 
        Retrieve or manage the currently authenticated Member's own profile.
        Route: GET/PUT/PATCH/DELETE /api/members/me/ 
        """
        member = request.user
        
        # Handle GET action
        if request.method == 'GET':
            serializer = self.get_serializer(member)
            return Response(serializer.data)
            
        # Handle PUT/PATCH updates to profile    
        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(member, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # Self account deletion request
        elif request.method == 'DELETE':
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['patch'], url_path='me/set_password')
    def me_set_password(self, request):
        """ 
        Update the currently authenticated user's own password.
        Route: PATCH /api/members/me/set_password/ 
        """
        member = request.user
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.set_password(serializer.validated_data['password'])
            member.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)