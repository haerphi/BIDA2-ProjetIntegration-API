from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
import django_filters

from core.accounts.permissions import IsAdminRole
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Member, Category
from .serializers import (
    MemberSerializer, 
    MemberCreateSerializer, 
    PasswordUpdateSerializer,
    MemberRoleUpdateSerializer,
    CategorySerializer
)
from django.contrib.auth.models import Group

class MemberFilter(django_filters.FilterSet):
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        method='filter_by_category'
    )

    class Meta:
        model = Member
        fields = [
            'ranking', 'gender', 'is_active', 'affiliation_number', 
            'email', 'first_name', 'last_name', 'postal_code', 
            'country', 'phone', 'birth_date'
        ]

    def filter_by_category(self, queryset, name, value):
        if not value:
            return queryset
            
        current_year = timezone.now().year
        q_obj = Q()
        
        if value.min_age is not None:
            max_birth_year = current_year - value.min_age
            q_obj &= Q(birth_date__year__lte=max_birth_year)
            
        if value.max_age is not None:
            min_birth_year = current_year - value.max_age
            q_obj &= Q(birth_date__year__gte=min_birth_year)
            
        if value.gender:
            q_obj &= Q(gender=value.gender)
            
        q_obj &= Q(birth_date__isnull=False)
        return queryset.filter(q_obj)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class MemberViewSet(viewsets.GenericViewSet):
    queryset = Member.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = MemberFilter
    search_fields = ['first_name', 'last_name', 'email']
    ordering_fields = ['last_name', 'ranking', 'first_name', 'created_at']


    def get_serializer_class(self):
        if self.action == 'create':
            return MemberCreateSerializer
        elif self.action in ['set_password', 'me_set_password']:
            return PasswordUpdateSerializer
        return MemberSerializer

    def get_permissions(self):
        admin_actions = ['create', 'update', 'partial_update', 'destroy', 'set_password', 'update_role', 'list_roles']
        if self.action in admin_actions:
            permission_classes = [IsAdminRole]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request):
        is_admin = IsAdminRole().has_permission(request, self)
        queryset = self.get_queryset()
        
        if not is_admin:
            current_year = timezone.now().year
            queryset = queryset.filter(
                contributions__status='completed', 
                contributions__created_at__year=current_year
            ).distinct()
            
        queryset = self.filter_queryset(queryset)

        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)

        pager = Paginator(queryset, limit)
        page_obj = pager.get_page(page)

        serializer = self.get_serializer(page_obj.object_list, many=True)

        return Response({
            "data": serializer.data,
            "limit": pager.per_page,
            "total": pager.count,
            "page": page_obj.number,
            "total_pages": pager.num_pages
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        member = self.get_object()
        serializer = self.get_serializer(member)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        member = self.get_object()
        serializer = self.get_serializer(member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        member = self.get_object()
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'])
    def set_password(self, request, pk=None):
        member = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.set_password(serializer.validated_data['password'])
            member.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='role')
    def update_role(self, request, pk=None):
        member = self.get_object()
        serializer = MemberRoleUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            role = serializer.validated_data['role']
            
            member.groups.clear()
            
            if role == 'admin':
                member.is_staff = True
                admin_group, _ = Group.objects.get_or_create(name='admin')
                member.groups.add(admin_group)
            elif role == 'staff':
                member.is_staff = True
                staff_group, _ = Group.objects.get_or_create(name='staff')
                member.groups.add(staff_group)
            else:
                member.is_staff = False
                role_group, _ = Group.objects.get_or_create(name=role)
                member.groups.add(role_group)
                
            member.save()
            return Response({'status': 'Role updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='roles')
    def list_roles(self, request):
        roles = Group.objects.values_list('name', flat=True)
        return Response(sorted(list(roles)), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'put', 'patch', 'delete'])
    def me(self, request):
        member = request.user

        if request.method == 'GET':
            serializer = self.get_serializer(member)
            return Response(serializer.data)

        elif request.method in ['PUT', 'PATCH']:
            partial = request.method == 'PATCH'
            serializer = self.get_serializer(member, data=request.data, partial=partial)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['patch'], url_path='me/set_password')
    def me_set_password(self, request):
        member = request.user
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            member.set_password(serializer.validated_data['password'])
            member.is_first_login = False
            member.save()
            return Response({'status': 'Password updated successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)