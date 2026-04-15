from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import Group
from .models import Member

class MemberAPITests(APITestCase):
    """
    Test suite for Member API endpoints ensuring permissions, data visibility,
    and CRUD operations work as expected for both regular members and admins.
    """
    def setUp(self):
        # Create default authorization groups
        admin_group, _ = Group.objects.get_or_create(name='admin')
        member_group, _ = Group.objects.get_or_create(name='member')

        # Setup an admin user
        self.admin_user = Member.objects.create_superuser(
            affiliation_number='ADM001',
            email='admin@test.com', 
            password='adminpassword',
            first_name='Admin', 
            last_name='User'
        )
        self.admin_user.groups.add(admin_group)

        # Setup a standard member user
        self.member_user = Member.objects.create_user(
            affiliation_number='MEM001',
            email='member@test.com', 
            password='memberpassword',
            first_name='Member', 
            last_name='User'
        )
        self.member_user.groups.add(member_group)

        # Setup a secondary member to test cross-account access restrictions
        self.other_member_user = Member.objects.create_user(
            affiliation_number='MEM002',
            email='other@test.com', 
            password='otherpassword',
            first_name='Other', 
            last_name='Member'
        )
        self.other_member_user.groups.add(member_group)

        # Base endpoint URL for member operations
        self.list_url = '/api/members/'

    def get_detail_url(self, member_id):
        """Helper to generate specific member detail URLs"""
        return f'/api/members/{member_id}/'

    def test_list_members_unauthenticated(self):
        """Ensure unauthenticated requests are blocked"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_list_members_authenticated(self):
        """Ensure authenticated members can list users, but PII (like email) is restricted"""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        data = response.data
        for item in data:
            if item['id'] != self.member_user.id:
                # Should not see other users' emails
                self.assertNotIn('email', item)
            else:
                # Should see own email
                self.assertIn('email', item)

    def test_list_members_admin(self):
        """Ensure admins can see all user details, including PII"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        for item in data:
            self.assertIn('email', item)

    def test_retrieve_member(self):
        """Ensure member detail retrieval successfully returns non-PII data for other users"""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(self.get_detail_url(self.other_member_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify email is hidden from regular users
        self.assertNotIn('email', response.data)

    def test_create_member_admin(self):
        """Ensure admins can create new member accounts"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'email': 'new@test.com',
            'affiliation_number': 'NEW001',
            'password': 'newpassword123',
            'firstname': 'New',
            'lastname': 'User',
            'role': 'member'
        }
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Member.objects.filter(email='new@test.com').exists())

    def test_create_member_non_admin(self):
        """Ensure standard members cannot create new accounts"""
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'email': 'new2@test.com',
            'affiliation_number': 'NEW002',
            'password': 'newpassword123',
            'firstname': 'New2',
            'lastname': 'User2'
        }
        response = self.client.post(self.list_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_member_admin(self):
        """Ensure admins can patch user profiles"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'firstname': 'UpdatedName',
            'lastname': 'User'
        }
        response = self.client.patch(self.get_detail_url(self.member_user.id), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_user.refresh_from_db()
        self.assertEqual(self.member_user.first_name, 'UpdatedName')

    def test_update_member_non_admin(self):
        """Ensure members cannot update profiles that don't belong to them"""
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'firstname': 'HackName'
        }
        response = self.client.patch(self.get_detail_url(self.other_member_user.id), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_member_admin(self):
        """Ensure admins can delete accounts"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.get_detail_url(self.other_member_user.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Member.objects.filter(id=self.other_member_user.id).exists())

    def test_delete_member_non_admin(self):
        """Ensure standard members cannot delete other accounts"""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete(self.get_detail_url(self.other_member_user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_get(self):
        """Ensure users can retrieve their own profile details using the /me/ endpoint"""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get('/api/members/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.member_user.id)

    def test_me_update(self):
        """Ensure users can update their own profile via the /me/ endpoint"""
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'firstname': 'MyNewName',
            'lastname': 'User',
            'email': 'member@test.com',
            'affiliation_number': 'MEM001' # Add the required Field for PUT
        }
        response = self.client.put('/api/members/me/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_user.refresh_from_db()
        self.assertEqual(self.member_user.first_name, 'MyNewName')

    def test_me_delete(self):
        """Ensure users can self-delete their account via the /me/ endpoint"""
        self.client.force_authenticate(user=self.member_user)
        response = self.client.delete('/api/members/me/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Member.objects.filter(id=self.member_user.id).exists())

    def test_me_set_password(self):
        """Ensure users can change their own password via the /me/set_password/ endpoint"""
        self.client.force_authenticate(user=self.member_user)
        payload = {
            'password': 'newsupasecretpassword'
        }
        response = self.client.patch('/api/members/me/set_password/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.member_user.refresh_from_db()
        self.assertTrue(self.member_user.check_password('newsupasecretpassword'))

    def test_admin_set_password_other_user(self):
        """Ensure admins can reset other users' passwords"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'password': 'hackedbypassed'
        }
        response = self.client.patch(f"{self.get_detail_url(self.other_member_user.id)}set_password/", payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.other_member_user.refresh_from_db()
        self.assertTrue(self.other_member_user.check_password('hackedbypassed'))