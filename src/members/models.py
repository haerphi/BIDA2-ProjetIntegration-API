from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class MemberManager(BaseUserManager):
    """
    Custom manager for the Member model.
    Allows creating regular users and superusers using an affiliation_number and email.
    """
    def create_user(self, affiliation_number, email, password=None, **extra_fields):
        if not affiliation_number:
            raise ValueError(_("The Affiliation Number must be set"))
        email = self.normalize_email(email)
        user = self.model(affiliation_number=affiliation_number, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, affiliation_number, email, password=None, **extra_fields):
        """
        Create a superuser and force required fields.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(affiliation_number, email, password, **extra_fields)


class Member(AbstractUser):
    """
    Custom user model representing members of the club.
    Inherits from AbstractUser to reuse core Django authentication functionalities.
    """
    class Meta:
        db_table = 'members'
        
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    # Remove standard username as we use affiliation_number instead
    username = None
    email = models.EmailField(_("email address"), unique=True)
    
    # Custom identifier for authentication
    affiliation_number = models.CharField(max_length=50, unique=True)
    
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.OTHER, null=True, blank=True)
    
    # External ID field for Google OAuth authentication
    google_subject_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    ranking = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = MemberManager()

    # Configure authentication required parameters
    USERNAME_FIELD = 'affiliation_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        """String representation showing user's full name"""
        return f"{self.first_name} {self.last_name}"