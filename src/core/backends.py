from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class AffiliationNumberBackend(ModelBackend):
    """
    Custom authentication backend that allows logging in using the affiliation_number.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        affiliation_number = kwargs.get('affiliation_number', username)
        if not affiliation_number:
            return None
            
        try:
            # Look up the user by affiliation number
            user = UserModel.objects.filter(affiliation_number=affiliation_number).first()
            
            # Authenticate the user if found, password matches, and the user is permitted to authenticate
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            # Return None to continue to the next authentication backend, if any
            return None
            
        return None