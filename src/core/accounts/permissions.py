from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Custom permission class that checks if the requesting user has administrative privileges.
    Verifies if the user is authenticated and either:
    - Has superuser status
    - Has staff status
    - Belongs to the 'admin' group
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        return request.user.is_superuser or request.user.is_staff or request.user.groups.filter(name='admin').exists()