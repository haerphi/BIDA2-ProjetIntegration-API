from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
    class Meta:
        db_table = 'members'
        
    class MemberRole(models.TextChoices):
        MEMBER = 'member', 'Member'
        ADMIN = 'admin', 'Admin'
        
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', null=True, blank=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    street = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, default=Gender.OTHER, null=True, blank=True)
    affiliation_number = models.CharField(max_length=50, null=True, blank=True)
    ranking = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=MemberRole.choices, default=MemberRole.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.firstname + ' ' + self.lastname
