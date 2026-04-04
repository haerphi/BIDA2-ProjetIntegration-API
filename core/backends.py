from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        email = kwargs.get('email', username)
        if not email:
            return None
        try:
            # We use filter(...).first() because Django's default User model doesn't enforce unique emails.
            # email__iexact makes the lookup case-insensitive.
            user = UserModel.objects.filter(email__iexact=email).first()
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        return None
