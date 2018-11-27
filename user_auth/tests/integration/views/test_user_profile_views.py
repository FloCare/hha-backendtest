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


class TestUpdateStaffView(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.pubnub_service_mock = MagicMock(name='pubnub_service_mock')
        pubnub_patcher = patch('user_auth.views.user_profile_views.PubnubService')
        pubnub_mock = pubnub_patcher.start()
        pubnub_mock.return_value = self.pubnub_service_mock
        self.addCleanup(pubnub_patcher.stop)

    def test_validates_admin_user(self):
        """Raises error if user is not admin"""
        url = reverse('update-staff', args=[uuid.uuid4()])
        payload = {}
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validates_body(self):
        """Raises error if user key is missing"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('update-staff', args=[uuid.uuid4()])
        payload = {}
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)

    def test_validates_blank_fields(self):
        """Raises error if fields are is blank"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('update-staff', args=[uuid.uuid4()])
        payload = {
            'user': {
                'firstName': '',
                'lastName': '',
                'email': '',
                'password': '',
                'phone': '',
                'role': ''
            }
        }
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)
        self.assertIn('firstName', response.data['error_message'])
        self.assertIn('lastName', response.data['error_message'])
        self.assertIn('email', response.data['error_message'])
        self.assertIn('password', response.data['error_message'])
        self.assertIn('phone', response.data['error_message'])
        self.assertIn('role', response.data['error_message'])

    def test_validates_null_fields(self):
        """Raises error if fields are null"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('update-staff', args=[uuid.uuid4()])
        payload = {
            'user': {
                'firstName': None,
                'lastName': None,
                'email': None,
                'password': None,
                'phone': None,
                'role': None
            }
        }
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)
        self.assertIn('firstName', response.data['error_message'])
        self.assertIn('lastName', response.data['error_message'])
        self.assertIn('email', response.data['error_message'])
        self.assertIn('password', response.data['error_message'])
        self.assertNotIn('phone', response.data['error_message'])
        self.assertIn('role', response.data['error_message'])

    def test_checks_for_same_org(self):
        """Raises error if user organizations don't match """
        test_helpers.make_user_admin(self.user_profile)

        org = test_helpers.create_organization()
        user_profile = test_helpers.create_user(org)
        url = reverse('update-staff', args=[user_profile.uuid])
        payload = {
            'user': {
                'firstName': 'bla',
            }
        }
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)

    def test_updates_requested_profile(self):
        """Updates profile and makes call to pubnub service"""
        test_helpers.make_user_admin(self.user_profile)

        user_profile = test_helpers.create_user(self.organization)
        url = reverse('update-staff', args=[user_profile.uuid])
        payload = {
            'user': {
                'firstName': 'new_first_name',
                'lastName': 'new_last_name',
                'email': 'new_email',
                'password': 'new_password',
                'phone': 'new_phone',
                'role': 'new_role'
            }
        }

        self.pubnub_service_mock.get_organization_channel.return_value = 'channel'
        self.pubnub_service_mock.get_user_update_message.return_value = 'user_update_message'

        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_profile = UserProfile.objects.get(uuid=user_profile.uuid)
        expected_user_data = {
            'first_name': payload['user']['firstName'],
            'last_name': payload['user']['lastName'],
            'email': payload['user']['email'],
            'password': payload['user']['password'],
            'contact_no': payload['user']['phone'],
            'role': payload['user']['role']
        }
        utils.compare_user(self, user_profile.user, expected_user_data)
        utils.compare_user_profile(self, user_profile, expected_user_data)

        self.pubnub_service_mock.get_organization_channel.assert_called_with(self.organization)
        self.pubnub_service_mock.get_user_update_message.assert_called_with(user_profile)
        self.pubnub_service_mock.publish.assert_called_with('channel', 'user_update_message')


class TestCreateStaffView(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def test_validates_admin_user(self):
        """Raises error if user is not admin"""
        url = reverse('create-staff')
        payload = {}
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validates_body(self):
        """Raises error if user key is missing"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('create-staff')
        payload = {}
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)

    def test_validates_blank_fields(self):
        """Raises error if fields are is blank"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('create-staff')
        payload = {
            'user': {
                'firstName': '',
                'lastName': '',
                'email': '',
                'password': '',
                'phone': '',
                'role': ''
            }
        }
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)
        self.assertIn('firstName', response.data['error_message'])
        self.assertIn('lastName', response.data['error_message'])
        self.assertIn('email', response.data['error_message'])
        self.assertIn('password', response.data['error_message'])
        self.assertIn('phone', response.data['error_message'])
        self.assertIn('role', response.data['error_message'])

    def test_validates_mandatory_fields(self):
        """Raises error if mandatory fields in payload are missing"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('create-staff')
        payload = {
            'user': {
                'email': 'adf3@g.com'
            }
        }
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)
        self.assertIn('firstName', response.data['error_message'])
        self.assertIn('lastName', response.data['error_message'])

    def test_validates_null_fields(self):
        """Raises error if fields are null"""
        test_helpers.make_user_admin(self.user_profile)

        url = reverse('create-staff')
        payload = {
            'user': {
                'firstName': None,
                'lastName': None,
                'email': None,
                'password': None,
                'phone': None,
                'role': None
            }
        }
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)
        self.assertIn('firstName', response.data['error_message'])
        self.assertIn('lastName', response.data['error_message'])
        self.assertIn('email', response.data['error_message'])
        self.assertIn('password', response.data['error_message'])
        self.assertNotIn('phone', response.data['error_message'])
        self.assertIn('role', response.data['error_message'])

    def test_creates_user(self):
        """Creates user and returns 201"""
        test_helpers.make_user_admin(self.user_profile)
        url = reverse('create-staff')
        payload = {
            'user': {
                'firstName': 'Gondor',
                'lastName': 'Calls',
                'email': 'For@aid.com',
                'password': 'And Rohan',
                'phone': 'Shall',
                'role': 'answer'
            }
        }
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user_profile = UserProfile.objects.get(user__first_name=payload['user']['firstName'])
        expected_user_data = {
            'first_name': payload['user']['firstName'],
            'last_name': payload['user']['lastName'],
            'email': payload['user']['email'],
            'password': payload['user']['password'],
            'contact_no': payload['user']['phone'],
            'role': payload['user']['role']
        }
        utils.compare_user(self, user_profile.user, expected_user_data)
        utils.compare_user_profile(self, user_profile, expected_user_data)

        user_org_access = UserOrganizationAccess.objects.get(user=user_profile)
        # Validate user org access
        self.assertEqual(user_org_access.user, user_profile)
        self.assertEqual(user_org_access.organization, self.organization)
        self.assertEqual(user_org_access.user_role, expected_user_data['role'])

    def test_raises_error_user_already_exists(self):
        """Raises error if user already exists with the given information"""
        test_helpers.make_user_admin(self.user_profile)
        url = reverse('create-staff')
        payload = {
            'user': {
                'firstName': 'Gondor',
                'lastName': 'Calls',
                'email': 'For@aid.com',
                'password': 'And Rohan',
                'phone': 'Shall',
                'role': 'answer'
            }
        }
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_ALREADY_EXISTS)