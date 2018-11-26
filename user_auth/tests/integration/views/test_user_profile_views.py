from backend import errors
from django.urls import reverse
from flocarebase.common import test_helpers
from rest_framework import status

import uuid
import logging

logger = logging.getLogger(__name__)


class TestGetStaffView(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def test_validates_admin_user(self):
        url = reverse('get-staff', args=[uuid.uuid4()])
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_raises_error(self):
        test_helpers.make_user_admin(self.user_profile)

        org = test_helpers.create_organization()
        user_profile = test_helpers.create_user(org)

        url = reverse('get-staff', args=[user_profile.uuid])
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)

    def test_success_response(self):
        test_helpers.make_user_admin(self.user_profile)
        user_profile = test_helpers.create_user(self.organization)
        url = reverse('get-staff', args=[user_profile.uuid])
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = {
            'user': {
                'id': str(user_profile.uuid),
                'old_id': None,
                'first_name': user_profile.user.first_name,
                'last_name': user_profile.user.last_name,
                'username': user_profile.user.username,
                'email': user_profile.user.email,
                'title': user_profile.title,
                'contact_no': user_profile.contact_no,
                'user_role': 'user_role'
            }
        }
        self.assertJSONEqual(str(response.content, encoding='utf8'), expected_response)

