from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from courts.models import Court
from members.models import MemberProfile

User = get_user_model()

class CourtAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            username='normal123',
            password='password123',
            email='normal@example.com'
        )
        if not hasattr(self.normal_user, 'profile'):
            MemberProfile.objects.create(user=self.normal_user, role='member', firstname='Normal', lastname='User', email=self.normal_user.email)
        else:
            self.normal_user.profile.role = 'member'
            self.normal_user.profile.save()

        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin123',
            password='password123',
            email='admin@example.com'
        )
        if not hasattr(self.admin_user, 'profile'):
            MemberProfile.objects.create(user=self.admin_user, role='admin', firstname='Admin', lastname='User', email=self.admin_user.email)
        else:
            self.admin_user.profile.role = 'admin'
            self.admin_user.profile.save()

        # Create a court
        self.court1 = Court.objects.create(number=1)
        self.court2 = Court.objects.create(number=2)

    def test_list_courts_unauthenticated(self):
        response = self.client.get('/api/courts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_courts_authenticated(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/courts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_court_normal_user_forbidden(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post('/api/courts/', {'number': 3})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_court_admin_user_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/courts/', {'number': 3})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Court.objects.count(), 3)

    def test_update_court_normal_user_forbidden(self):
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.patch(f'/api/courts/{self.court1.id}/', {'number': 10})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_court_admin_user_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(f'/api/courts/{self.court1.id}/', {'number': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.court1.refresh_from_db()
        self.assertEqual(self.court1.number, 10)

    def test_delete_court_admin_user_allowed(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/courts/{self.court1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Court.objects.count(), 1)
