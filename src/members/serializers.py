from rest_framework import serializers
from django.contrib.auth.models import Group
from django.utils import timezone
from .models import Member, Category


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'min_age', 'max_age', 'gender']


class MemberSerializer(serializers.ModelSerializer):
    """
    Standard ModelSerializer for returning member information.
    Provides logic to dynamically determine member's role and restrict visibility of certain fields.
    """
    firstname = serializers.CharField(source='first_name', required=True)
    lastname = serializers.CharField(source='last_name', required=True)
    role = serializers.SerializerMethodField()
    contribution_paid = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id', 'firstname', 'lastname', 'email', 'street', 'city',
            'postal_code', 'country', 'phone', 'birth_date', 'gender',
            'affiliation_number', 'ranking', 'is_active', 'role', 'contribution_paid', 'categories', 'created_at'
        ]

        read_only_fields = ['created_at']

    def get_role(self, obj):
        """
        Determine role dynamically checking standard permissions or group memberships.
        Returns 'admin' or defaults to 'member'.
        """
        if obj.is_superuser or obj.is_staff or obj.groups.filter(name='admin').exists():
            return 'admin'
        return 'member'

    def get_contribution_paid(self, obj):
        """
        Returns boolean indicating whether the member has paid their contribution for the current year.
        """
        return obj.has_paid_contribution()

    def get_categories(self, obj):
        """
        Determine eligible categories for the member based on age and gender.
        """
        if not obj.birth_date:
            return []
        
        current_year = timezone.now().year
        age = current_year - obj.birth_date.year

        all_categories = self.context.get('all_categories')
        if all_categories is None:
            all_categories = list(Category.objects.all())
            self.context['all_categories'] = all_categories

        matching_categories = []
        for cat in all_categories:
            if cat.gender and obj.gender != cat.gender:
                continue
            if cat.min_age is not None and age < cat.min_age:
                continue
            if cat.max_age is not None and age > cat.max_age:
                continue
            matching_categories.append(cat.name)
            
        return matching_categories

    def to_representation(self, instance):
        """
        Filter output fields based on the requesting user's authorization level.
        Non-admins can only see the email field for their own account, otherwise it is hidden.
        """
        representation = super().to_representation(instance)
        request = self.context.get('request')

        is_admin = False
        if request and request.user.is_authenticated:
            # Grant access if requesting user has admin-level capabilities
            if request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='admin').exists():
                is_admin = True

        # Grant access if user is viewing their own profile
        if request and hasattr(request, 'user') and request.user == instance:
            is_admin = True

        # Omit 'email' field for unauthorized users
        if not is_admin:
            representation.pop('email', None)

        return representation


class MemberCreateSerializer(serializers.ModelSerializer):
    """
    Serializer specifically for creating new Member entities with required passwords and roles.
    Assures roles get mapped correctly to Django auth groups.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    firstname = serializers.CharField(source='first_name', required=True)
    lastname = serializers.CharField(source='last_name', required=True)
    role = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Member
        fields = [
            'id', 'firstname', 'lastname', 'email', 'street', 'city',
            'postal_code', 'country', 'phone', 'birth_date', 'gender',
            'affiliation_number', 'ranking', 'is_active', 'role', 'created_at', 'password'
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        """
        Custom create routine to handle hashing user passwords, determining structural permissions based on role
        string, and assigning users to matching auth groups.
        """
        # Pop sensitive and custom field info
        password = validated_data.pop('password')
        role = validated_data.pop('role', 'member')
        
        # Build standard model instance
        member = Member(**validated_data)
        member.set_password(password)
        
        # Make the account an admin internally if requested
        if role == 'admin':
            member.is_staff = True
            
        member.save()

        # Add user to auth_groups depending on assigned role
        admin_group, _ = Group.objects.get_or_create(name='admin')
        member_group, _ = Group.objects.get_or_create(name='member')
        
        if role == 'admin' or member.is_staff or member.is_superuser:
            member.groups.add(admin_group)
        else:
            member.groups.add(member_group)

        return member


class PasswordUpdateSerializer(serializers.Serializer):
    """
    Basic serializer to receive and update user passwords.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

class MemberRoleUpdateSerializer(serializers.Serializer):
    """
    Serializer to receive and update a user's role.
    """
    role = serializers.CharField(required=True)