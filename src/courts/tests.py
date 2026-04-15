from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from courts.models import Court, Reservation
from members.models import Member

User = get_user_model()

class CourtAPITests(TestCase):
    """
    Test suite for Court basic CRUD API endpoints.
    Ensures that standard users can only view courts, while admins can modify them.
    """
    def setUp(self):
        self.client = APIClient()
        admin_group, _ = Group.objects.get_or_create(name='admin')
        member_group, _ = Group.objects.get_or_create(name='member')
        
        # Create normal user
        self.normal_user = User.objects.create_user(
            affiliation_number='NRM001',
            password='password123',
            email='normal@example.com',
            first_name='Normal',
            last_name='User'
        )
        self.normal_user.groups.add(member_group)

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            affiliation_number='ADM001',
            password='password123',
            email='admin@example.com',
            first_name='Admin',
            last_name='User'
        )
        self.admin_user.groups.add(admin_group)

        # Create a court
        self.court1 = Court.objects.create(number=1)
        self.court2 = Court.objects.create(number=2)

    def test_list_courts_unauthenticated(self):
        """Ensure unauthenticated users cannot list courts"""
        response = self.client.get('/api/courts/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_courts_authenticated(self):
        """Ensure authenticated members can view the list of courts"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get('/api/courts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_court_normal_user_forbidden(self):
        """Ensure regular members cannot create new courts"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post('/api/courts/', {'number': 3})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_court_admin_user_allowed(self):
        """Ensure admins can create new courts"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post('/api/courts/', {'number': 3})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Court.objects.count(), 3)

    def test_update_court_normal_user_forbidden(self):
        """Ensure regular members cannot update court configurations"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.patch(f'/api/courts/{self.court1.id}/', {'number': 10})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_court_admin_user_allowed(self):
        """Ensure admins can update court configurations"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(f'/api/courts/{self.court1.id}/', {'number': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.court1.refresh_from_db()
        self.assertEqual(self.court1.number, 10)

    def test_delete_court_admin_user_allowed(self):
        """Ensure admins can delete courts"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/courts/{self.court1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Court.objects.count(), 1)

class CourtBookingTests(TestCase):
    """
    Test suite specifically for Court Booking logic.
    Tests valid player combinations, date scheduling, and overlap prevention.
    """
    def setUp(self):
        self.client = APIClient()
        member_group, _ = Group.objects.get_or_create(name='member')
        
        # Setup multiple test users to simulate singles and doubles matches
        self.user1 = User.objects.create_user(affiliation_number='U001', password='pw', email='u1@a.com', first_name='U', last_name='1')
        self.user1.groups.add(member_group)
        self.user2 = User.objects.create_user(affiliation_number='U002', password='pw', email='u2@a.com', first_name='U', last_name='2')
        self.user2.groups.add(member_group)
        self.user3 = User.objects.create_user(affiliation_number='U003', password='pw', email='u3@a.com', first_name='U', last_name='3')
        self.user3.groups.add(member_group)
        self.user4 = User.objects.create_user(affiliation_number='U004', password='pw', email='u4@a.com', first_name='U', last_name='4')
        self.user4.groups.add(member_group)
        
        self.court = Court.objects.create(number=1)
        self.client.force_authenticate(user=self.user1)

    def test_book_successful_1_member(self):
        """Ensure booking succeeds when requesting player + 1 opponent (Singles)"""
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.user2.id],
            'date_time': future_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reservation.objects.count(), 1)
        booking = Reservation.objects.first()
        self.assertEqual(booking.players.count(), 2)

    def test_book_successful_3_members(self):
        """Ensure booking succeeds when requesting player + 3 opponents (Doubles)"""
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.user2.id, self.user3.id, self.user4.id],
            'date_time': future_time.isoformat(),
            'duration': 120
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        booking = Reservation.objects.first()
        self.assertEqual(booking.players.count(), 4)

    def test_book_invalid_duration(self):
        """Ensure bookings cannot have non-standard durations (e.g., 90 minutes)"""
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.user2.id],
            'date_time': future_time.isoformat(),
            'duration': 90
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_invalid_members_count(self):
        """Ensure bookings fail if an incorrect number of opponents is passed (e.g., 2 opponents -> total 3 players, invalid for tennis)"""
        future_time = timezone.now() + timedelta(days=1)
        data = {
            'members': [self.user2.id, self.user3.id],
            'date_time': future_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_in_past(self):
        """Ensure users cannot book courts for times that have already occurred"""
        past_time = timezone.now() - timedelta(days=1)
        data = {
            'members': [self.user2.id],
            'date_time': past_time.isoformat(),
            'duration': 60
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_book_overlap(self):
        """Ensure users cannot book courts during an existing active reservation timeslot"""
        future_time = timezone.now() + timedelta(days=1)
        # Ensure we are on an exact hour to avoid microseconds flakiness
        future_time = future_time.replace(minute=0, second=0, microsecond=0)
        data = {
            'members': [self.user2.id],
            'date_time': future_time.isoformat(),
            'duration': 120
        }
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Try to overlap by 60 minutes into the existing 120 minute booking
        overlap_time = future_time + timedelta(minutes=60)
        data['date_time'] = overlap_time.isoformat()
        
        res = self.client.post(f'/api/courts/{self.court.id}/book/', data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_time', res.data)