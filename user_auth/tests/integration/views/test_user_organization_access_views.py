from django.urls import reverse
from flocarebase.common import test_helpers
from rest_framework import status
from user_auth.models import *

import logging

logger = logging.getLogger(__name__)


class TestUserOrganizationView(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def test_validates_admin_user(self):
        """Returns 403 if user is not admin"""
        url = reverse('org-access')
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_with_no_filters(self):
        """Returns results sorted by first name if no params are passed"""
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([self.user_profile, user_profile_1], key=lambda user_profile: user_profile.user.first_name)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        user_2 = users_sorted[1]
        user_org_access_2 = UserOrganizationAccess.objects.get(user=user_2)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    },
                    {
                        'id': str(user_2.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_2.user.first_name,
                        'last_name': user_2.user.last_name,
                        'username': user_2.user.username,
                        'contact_no': user_2.contact_no,
                        'email': user_2.user.email,
                        'user_role': user_org_access_2.user_role
                    },
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_sort_filters(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        url = url + '?sort=last_name'
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([self.user_profile, user_profile_1],
                              key=lambda user_profile: user_profile.user.last_name)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        user_2 = users_sorted[1]
        user_org_access_2 = UserOrganizationAccess.objects.get(user=user_2)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    },
                    {
                        'id': str(user_2.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_2.user.first_name,
                        'last_name': user_2.user.last_name,
                        'username': user_2.user.username,
                        'contact_no': user_2.contact_no,
                        'email': user_2.user.email,
                        'user_role': user_org_access_2.user_role
                    },
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_sort_filters_and_order(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        url = url + '?sort=last_name&order=DESC'
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([self.user_profile, user_profile_1],
                              key=lambda user_profile: user_profile.user.last_name, reverse=True)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        user_2 = users_sorted[1]
        user_org_access_2 = UserOrganizationAccess.objects.get(user=user_2)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    },
                    {
                        'id': str(user_2.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_2.user.first_name,
                        'last_name': user_2.user.last_name,
                        'username': user_2.user.username,
                        'contact_no': user_2.contact_no,
                        'email': user_2.user.email,
                        'user_role': user_org_access_2.user_role
                    },
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_size_filter(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        url = url + '?size=1'
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([self.user_profile, user_profile_1],
                              key=lambda user_profile: user_profile.user.last_name)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    }
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_query_filter(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization, first_name='Maximus')

        url = reverse('org-access')
        url = url + '?query=Max'
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_1 = user_profile_1
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    }
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_ids_query(self):
        test_helpers.make_user_admin(self.user_profile)
        test_helpers.create_user(self.organization)
        user_profile_2 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        url = url + '?ids=' + str(self.user_profile.uuid) + '&ids=' + str(user_profile_2.uuid)
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([self.user_profile, user_profile_2],
                              key=lambda user_profile: user_profile.user.last_name)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        user_2 = users_sorted[1]
        user_org_access_2 = UserOrganizationAccess.objects.get(user=user_2)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    },
                    {
                        'id': str(user_2.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_2.user.first_name,
                        'last_name': user_2.user.last_name,
                        'username': user_2.user.username,
                        'contact_no': user_2.contact_no,
                        'email': user_2.user.email,
                        'user_role': user_org_access_2.user_role
                    },
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_all_filters(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization, last_name='abc_1')
        user_profile_4 = test_helpers.create_user(self.organization, last_name='bac_2')
        user_profile_3 = test_helpers.create_user(self.organization, last_name='abc_3')
        user_profile_2 = test_helpers.create_user(self.organization, last_name='abc_2')

        url = reverse('org-access')
        url = url + '?sort=last_name&order=DESC&size=2&query=abc'
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        users_sorted = sorted([user_profile_1, user_profile_3, user_profile_2],
                              key=lambda user_profile: user_profile.user.last_name, reverse=True)
        user_1 = users_sorted[0]
        user_org_access_1 = UserOrganizationAccess.objects.get(user=user_1)
        user_2 = users_sorted[1]
        user_org_access_2 = UserOrganizationAccess.objects.get(user=user_2)
        expected_response = {
            'organization':
                {
                    'id': str(self.organization.uuid),
                    'name': self.organization.name,
                    'type': self.organization.type,
                    'contact_no': self.organization.contact_no,
                    'address': None
                },
            'users':
                [
                    {
                        'id': str(user_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_1.user.first_name,
                        'last_name': user_1.user.last_name,
                        'username': user_1.user.username,
                        'contact_no': user_1.contact_no,
                        'email': user_1.user.email,
                        'user_role': user_org_access_1.user_role
                    },
                    {
                        'id': str(user_2.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_2.user.first_name,
                        'last_name': user_2.user.last_name,
                        'username': user_2.user.username,
                        'contact_no': user_2.contact_no,
                        'email': user_2.user.email,
                        'user_role': user_org_access_2.user_role
                    },
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)
