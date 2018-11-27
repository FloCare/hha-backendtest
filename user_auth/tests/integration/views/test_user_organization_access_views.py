from backend import errors
from django.urls import reverse
from flocarebase.common import test_helpers
from rest_framework import status
from unittest.mock import patch, MagicMock
from user_auth.models import *
from user_auth.tests.integration.common import utils

import json
import uuid
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
        """Returns results if no params are passed"""
        test_helpers.make_user_admin(self.user_profile)
        user_profile_1 = test_helpers.create_user(self.organization)

        url = reverse('org-access')
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_org_access = UserOrganizationAccess.objects.get(user=self.user_profile)
        user_org_access_1 = UserOrganizationAccess.objects.get(user=self.user_profile)
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
                        'id': str(self.user_profile.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': self.user_profile.user.first_name,
                        'last_name': self.user_profile.user.last_name,
                        'username': self.user_profile.user.username,
                        'contact_no': self.user_profile.contact_no,
                        'email': self.user_profile.user.email,
                        'user_role': user_org_access.user_role
                    },
                    {
                        'id': str(user_profile_1.uuid),
                        'old_id': None,
                        'title': '',
                        'first_name': user_profile_1.user.first_name,
                        'last_name': user_profile_1.user.last_name,
                        'username': user_profile_1.user.username,
                        'contact_no': user_profile_1.contact_no,
                        'email': user_profile_1.user.email,
                        'user_role': user_org_access_1.user_role
                    }
                ]
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

    def test_with_sort_filters(self):
        self.fail()

    def test_with_size_filter(self):
        self.fail()

    def test_with_query_filter(self):
        self.fail()

    def test_with_all_filters(self):
        self.fail()
