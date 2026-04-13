from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from courts.models import Court, Reservation
from members.models import Member

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
            Member.objects.create(user=self.normal_user, role='member', firstname='Normal', lastname='User', email=self.normal_user.email)
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
            Member.objects.create(user=self.admin_user, role='admin', firstname='Admin', lastname='User', email=self.admin_user.email)
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

class CourtBookingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.user1 = User.objects.create_user(username='user1', password='pw')
        self.profile1 = Member.objects.create(user=self.user1, role='member', firstname='U', lastname='1', email='u1@a.com')
        
        self.user2 = User.objects.create_user(username='user2', password='pw')
        self.profile2 = Member.objects.create(user=self.user2, role='member', firstname='U', lastname='2', email='u2@a.com')
        
        self.user3 = User.objects.create_user(username='user3', password='pw')
        self.profile3 = Member.objects.create(user=self.user3, role='member', firstname='U', lastname='3', email='u3@a.com')
        
        self.user4 = User.objects.create_user(username='user4', password='pw')
        self.profile4 = Member.objects.create(user=self.user4, role='member', firstname='U', lastname='4', email='u4@a.com')
        
        self.court = Court.objects.create(number=1)
        self.client.force_authenticate(user=self.user1)

    def test_book_successful_1_member(self):
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.profile2.id],
            'date_time': future_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        booking = Reservation.objects.first()
        self.assertEqual(booking.players.count(), 2)

    def test_book_successful_3_members(self):
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.profile2.id, self.profile3.id, self.profile4.id],
            'date_time': future_time.isoformat(),
            'duration': 120
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking = Reservation.objects.first()
        self.assertEqual(booking.players.count(), 4)

    def test_book_invalid_duration(self):
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.profile2.id],
            'date_time': future_time.isoformat(),
            'duration': 90
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_invalid_members_count(self):
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.profile2.id, self.profile3.id],
            'date_time': future_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_in_past(self):
        past_time = timezone.now() - timedelta(days=1)
        data = {
            'members': [self.profile2.id],
            'date_time': past_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_overlap(self):
        future_time = timezone.now() + timedelta(days=1)
        # Ensure we are on an exact hour to avoid microseconds flakiness
        future_time = future_time.replace(minute=0, second=0, microsecond=0)
        data = {
            'members': [self.profile2.id],
            'date_time': future_time.isoformat(),
            'duration': 120
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        overlap_time = future_time + timedelta(minutes=60)
        data['date_time'] = overlap_time.isoformat()
        
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_time', res.data)
