from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import MemberProfile

class MemberProfileAPITests(APITestCase):
    def setUp(self):
        # Admin user
        self.admin_user = User.objects.create_user(username='admin@test.com', email='admin@test.com', password='adminpassword')
        self.admin_profile = MemberProfile.objects.create(
            user=self.admin_user, 
            firstname='Admin', 
            lastname='User', 
            email='admin@test.com',
            role=MemberProfile.MemberRole.ADMIN
        )

        # Member user
        self.member_user = User.objects.create_user(username='member@test.com', email='member@test.com', password='memberpassword')
        self.member_profile = MemberProfile.objects.create(
            user=self.member_user, 
            firstname='Member', 
            lastname='User', 
            email='member@test.com',
            role=MemberProfile.MemberRole.MEMBER
        )

        # Test Member
        self.other_member_user = User.objects.create_user(username='other@test.com', email='other@test.com', password='otherpassword')
        self.other_member_profile = MemberProfile.objects.create(
            user=self.other_member_user, 
            firstname='Other', 
            lastname='Member', 
            email='other@test.com',
            role=MemberProfile.MemberRole.MEMBER
        )

        self.list_url = '/api/members/'

    def get_detail_url(self, profile_id):
        return f'/api/members/{profile_id}/'

    def test_list_members_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_list_members_authenticated(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        data = response.data
        for item in data:
            if item['id'] != self.member_profile.id:
                self.assertNotIn('email', item)
            else:
                self.assertIn('email', item)

    def test_list_members_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        for item in data:
            self.assertIn('email', item)

    def test_retrieve_member(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.get_detail_url(self.other_member_profile.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # User is not admin
        self.assertNotIn('email', response.data)

    def test_create_member_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'email': 'new@test.com',
            'password': 'newpassword123',
            'firstname': 'New',
            'lastname': 'User',
            'role': 'member'
        }
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='new@test.com').exists())
        self.assertTrue(MemberProfile.objects.filter(email='new@test.com').exists())

    def test_create_member_non_admin(self):
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'email': 'new2@test.com',
            'password': 'newpassword123',
            'firstname': 'New2',
            'lastname': 'User2'
        }
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_member_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'firstname': 'UpdatedName',
            'lastname': 'User'
        }
        response = self.client.patch(self.get_detail_url(self.member_profile.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.firstname, 'UpdatedName')

    def test_update_member_non_admin(self):
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'firstname': 'HackName'
        }
        response = self.client.patch(self.get_detail_url(self.other_member_profile.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_member_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.get_detail_url(self.other_member_profile.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MemberProfile.objects.filter(id=self.other_member_profile.id).exists())

    def test_delete_member_non_admin(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.get_detail_url(self.other_member_profile.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_get(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/members/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.member_profile.id)

    def test_me_update(self):
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'firstname': 'MyNewName',
            'lastname': 'User',
            'email': 'member@test.com'
        }
        response = self.client.put('/api/members/me/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.firstname, 'MyNewName')

    def test_me_delete(self):
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete('/api/members/me/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.member_user.id).exists())

    def test_me_set_password(self):
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'password': 'newsupasecretpassword'
        }
        response = self.client.patch('/api/members/me/set_password/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_user.refresh_from_db()
        self.assertTrue(self.member_user.check_password('newsupasecretpassword'))

    def test_admin_set_password_other_user(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'password': 'hackedbypassed'
        }
        response = self.client.patch(f"{self.get_detail_url(self.other_member_profile.id)}set_password/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_member_user.refresh_from_db()
        self.assertTrue(self.other_member_user.check_password('hackedbypassed'))
