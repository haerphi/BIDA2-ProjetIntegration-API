from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class AffiliationNumberBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        affiliation_number = kwargs.get('affiliation_number', username)
        if not affiliation_number:
            return None
        try:
            user = UserModel.objects.filter(profile__affiliation_number=affiliation_number).first()
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        return None
