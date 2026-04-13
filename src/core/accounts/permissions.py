from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Checks if the user has the 'admin' role in their Member.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        profile = getattr(request.user, 'profile', None)
        return profile and profile.role == 'admin'