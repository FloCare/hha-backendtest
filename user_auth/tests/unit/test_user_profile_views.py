from backend import errors
from rest_framework import status
from flocarebase.common import test_helpers
from flocarebase.exceptions import InvalidPayloadError
from rest_framework.permissions import IsAuthenticated
from unittest.mock import MagicMock
from user_auth.exceptions import UserAlreadyExistsError, UserDoesNotExistError, UserOrgAccessDoesNotExistError
from user_auth.views import GetStaffView, UpdateStaffView, CreateStaffView, DeleteStaffView, UserProfileView
from user_auth.permissions import IsAdminForOrg

import logging
import uuid

logger = logging.getLogger(__name__)


class TestGetStaffView(test_helpers.BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)

    def test_permission_classes(self):
        self.assertEqual(GetStaffView.permission_classes, (IsAuthenticated, IsAdminForOrg))

    def test_validates_same_org(self):
        test_helpers.make_user_admin(self.user_profile)
        user_oa_mock = MagicMock(name='user_org_mock', organization = self.organization)
        org_1 = test_helpers.create_organization()
        user_1_uuid = uuid.uuid4()
        user_1_oa_mock = MagicMock(name='user_1_org_access', organization=org_1)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_oa_mock
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_oa_mock
        request = MagicMock(name='request', user=self.user_profile.user)
        response = GetStaffView().get(request, user_1_uuid)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1_uuid)

    def test_returns_staff_data(self):
        test_helpers.make_user_admin(self.user_profile)
        user_oa_mock = MagicMock(name='user_org_mock', organization=self.organization)
        user_1 = test_helpers.create_user(self.organization)
        user_1_oa_mock = MagicMock(name='user_1_org_access', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_oa_mock
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_oa_mock

        user_details_ser_mock = MagicMock(name='user_details_ser_mock')
        user_details_ser_class_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserDetailsResponseSerializer', user_details_ser_mock)
        serializer_mock = MagicMock(name='serializer_mock', data=1)
        user_details_ser_class_mock.return_value = serializer_mock
        request = MagicMock(name='request', user=self.user_profile.user)
        response = GetStaffView().get(request, user_1.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1.uuid)
        user_details_ser_class_mock.assert_called_once_with({'user': user_1_oa_mock})
        self.assertEqual(response.data, serializer_mock.data)


class TestUpdateStaffView(test_helpers.BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)
        self.user_ds_mock = MagicMock(name='user_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserDataService', self.user_ds_mock)
        self.pubnub_service_mock = MagicMock(name='pubnub_service_mock')
        self.patch_class('user_auth.views.user_profile_views.PubnubService', self.pubnub_service_mock)

    def test_permission_classes(self):
        self.assertEqual(UpdateStaffView.permission_classes, (IsAuthenticated, IsAdminForOrg))

    def test_validate_and_format_request_user_key(self):
        """Raises error if request doesn't have user key"""
        request = MagicMock(name='request', data={})
        with self.assertRaises(InvalidPayloadError) as e:
            UpdateStaffView().validate_and_format_request(request)
            self.assertEqual(e.message, 'user data missing')

    def test_validate_and_format_request_validates_blank(self):
        """"Raises error if fields are blank"""
        data = {
            'user': {
                'firstName': '',
                'lastName': '',
                'email': '',
                'password': '',
                'phone': '',
                'role': '',
            }
        }
        request = MagicMock(name='request', data=data)
        with self.assertRaises(InvalidPayloadError) as e:
            UpdateStaffView().validate_and_format_request(request)
            self.assertIn('firstName', e.message)
            self.assertIn('lastName', e.message)
            self.assertIn('email', e.message)
            self.assertIn('password', e.message)
            self.assertIn('phone', e.message)
            self.assertIn('role', e.message)

    def test_validate_and_format_request_validates_null(self):
        """Raises error if fields are null"""
        data = {
            'user': {
                'firstName': None,
                'lastName': None,
                'email': None,
                'password': None,
                'phone': None,
                'role': None,
            }
        }
        request = MagicMock(name='request', data=data)
        with self.assertRaises(InvalidPayloadError) as e:
            UpdateStaffView().validate_and_format_request(request)
            self.assertIn('firstName', e.message)
            self.assertIn('lastName', e.message)
            self.assertIn('email', e.message)
            self.assertIn('password', e.message)
            self.assertIn('role', e.message)

    def test_validate_and_format_request(self):
        """Returns formatted object as expected"""
        data = {
            'user': {
                'firstName': 'new_first_name',
                'lastName': 'new_last_name',
                'email': 'new_email',
                'password': 'new_password',
                'phone': 'new_phone',
                'role': 'role',
            }
        }
        request = MagicMock(name='request', data=data)
        formatted_data = UpdateStaffView().validate_and_format_request(request)
        self.assertEqual(formatted_data['first_name'], data['user']['firstName'])
        self.assertEqual(formatted_data['last_name'], data['user']['lastName'])
        self.assertEqual(formatted_data['email'], data['user']['email'])
        self.assertEqual(formatted_data['password'], data['user']['password'])
        self.assertEqual(formatted_data['contact_no'], data['user']['phone'])
        self.assertEqual(formatted_data['role'], data['user']['role'])

    def test_put_data_invalid(self):
        request = MagicMock(name='request', data={})
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org

        response = UpdateStaffView().put(request, uuid.uuid4())
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)

    def test_put_different_org(self):
        request = MagicMock(name='request', data={'user': {}})
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        user_1_org = MagicMock(name='user_1_org', organization=1)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_org

        user_id = uuid.uuid4()
        response = UpdateStaffView().put(request, user_id)

        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)

    def test_put_update(self):
        request = MagicMock(name='request', data={'user': {}})
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        user_1 = MagicMock('user_1')
        user_1_org = MagicMock(name='user_1_org', organization=self.organization, user=user_1)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_org
        formatted_request = MagicMock(name='formatted_request')
        validate_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.UpdateStaffView.validate_and_format_request', formatted_request)
        channel = 'channel'
        message = 'message'
        self.pubnub_service_mock.get_organization_channel.return_value = channel
        self.pubnub_service_mock.get_user_update_message.return_value = message

        user_id = uuid.uuid4()
        response = UpdateStaffView().put(request, user_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_id)
        validate_method_mock.assert_called_once_with(request)
        self.user_ds_mock.update_user_by_uuid.assert_called_once_with(user_id, formatted_request)
        self.pubnub_service_mock.get_organization_channel.assert_called_once_with(user_org.organization)
        self.pubnub_service_mock.get_user_update_message.assert_called_once_with(user_1_org.user)
        self.pubnub_service_mock.publish.assert_called_once_with(channel, message)


class TestCreateStaffView(test_helpers.BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)
        self.user_ds_mock = MagicMock(name='user_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserDataService', self.user_ds_mock)

    def test_permission_classes(self):
        self.assertEqual(CreateStaffView.permission_classes, (IsAuthenticated, IsAdminForOrg))

    def test_validate_and_format_request_user_key(self):
        """Raises error if request doesn't have user key"""
        request = MagicMock(name='request', data={})
        with self.assertRaises(InvalidPayloadError) as e:
            CreateStaffView().validate_and_format_request(request)
            self.assertEqual(e.message, 'user data missing')

    def test_validate_and_format_request_validates_blank(self):
        """"Raises error if fields are blank"""
        data = {
            'user': {
                'firstName': '',
                'lastName': '',
                'email': '',
                'password': '',
                'phone': '',
                'role': '',
            }
        }
        request = MagicMock(name='request', data=data)
        with self.assertRaises(InvalidPayloadError) as e:
            CreateStaffView().validate_and_format_request(request)
            self.assertIn('firstName', e.message)
            self.assertIn('lastName', e.message)
            self.assertIn('email', e.message)
            self.assertIn('password', e.message)
            self.assertIn('phone', e.message)
            self.assertIn('role', e.message)

    def test_validate_and_format_request_validates_null(self):
        """Raises error if fields are null"""
        data = {
            'user': {
                'firstName': None,
                'lastName': None,
                'email': None,
                'password': None,
                'phone': None,
                'role': None,
            }
        }
        request = MagicMock(name='request', data=data)
        with self.assertRaises(InvalidPayloadError) as e:
            CreateStaffView().validate_and_format_request(request)
            self.assertIn('firstName', e.message)
            self.assertIn('lastName', e.message)
            self.assertIn('email', e.message)
            self.assertIn('password', e.message)
            self.assertIn('role', e.message)

    def test_validate_and_format_request(self):
        """Returns formatted object as expected"""
        data = {
            'user': {
                'firstName': 'new_first_name',
                'lastName': 'new_last_name',
                'email': 'new_email',
                'password': 'new_password',
                'phone': 'new_phone',
                'role': 'role',
            }
        }
        request = MagicMock(name='request', data=data)
        formatted_data = CreateStaffView().validate_and_format_request(request)
        self.assertEqual(formatted_data['first_name'], data['user']['firstName'])
        self.assertEqual(formatted_data['last_name'], data['user']['lastName'])
        self.assertEqual(formatted_data['email'], data['user']['email'])
        self.assertEqual(formatted_data['password'], data['user']['password'])
        self.assertEqual(formatted_data['contact_no'], data['user']['phone'])
        self.assertEqual(formatted_data['role'], data['user']['role'])

    def test_post_data_invalid(self):
        """Returns 400 if data is not valid"""
        request = MagicMock(name='request', data={})
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org

        response = CreateStaffView().post(request)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.DATA_INVALID)

    def test_post_create_duplicate_user(self):
        """Returns 409 if trying to create user with same data"""
        user_data = MagicMock(name='user_data')
        request = MagicMock(name='request', data=user_data)
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        formatted_request = MagicMock(name='formatted_request')
        validate_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.CreateStaffView.validate_and_format_request', formatted_request)
        self.user_ds_mock.create_user.side_effect = UserAlreadyExistsError(1)
        response = CreateStaffView().post(request)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        validate_method_mock.assert_called_once_with(request)
        self.user_ds_mock.create_user.assert_called_once_with(formatted_request, user_org.organization)

    def test_post_create(self):
        """Call user data service to create user with with the given data"""
        user_data = MagicMock(name='user_data')
        request = MagicMock(name='request', data=user_data)
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        formatted_request = MagicMock(name='formatted_request')
        validate_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.CreateStaffView.validate_and_format_request', formatted_request)

        response = CreateStaffView().post(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(request.user.profile)
        validate_method_mock.assert_called_once_with(request)
        self.user_ds_mock.create_user.assert_called_once_with(formatted_request, user_org.organization)


class TestDeleteStaffView(test_helpers.BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)
        self.user_ds_mock = MagicMock(name='user_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserDataService', self.user_ds_mock)

    def test_permission_classes(self):
        self.assertEqual(DeleteStaffView.permission_classes, (IsAuthenticated, IsAdminForOrg))

    def test_delete_fails_if_user_does_not_exist(self):
        request = MagicMock(name='request')
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        user_1_uuid = uuid.uuid4()
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.side_effect = UserDoesNotExistError(user_1_uuid)

        response = DeleteStaffView().delete(request, user_1_uuid)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1_uuid)

    def test_delete_fails_if_different_org(self):
        request = MagicMock(name='request')
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        user_1 = MagicMock(name='user_1', uuid=uuid.uuid4())
        user_1_org = MagicMock(name='user_1_org', organization=2)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_org

        response = DeleteStaffView().delete(request, user_1.uuid)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1.uuid)

    def test_deletes_user(self):
        request = MagicMock(name='request')
        request.user.profile = self.user_profile
        user_org = MagicMock(name='user_org', organization=self.organization)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org
        user_1 = MagicMock(name='user_1', uuid=uuid.uuid4())
        user_1_org = MagicMock(name='user_1_org', organization=self.organization, user=user_1)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_org

        response = DeleteStaffView().delete(request, user_1.uuid)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1.uuid)
        self.user_ds_mock.delete_user_by_user_profile.assert_called_once_with(user_1)


class TestUserProfileView(test_helpers.BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)
        self.user_ds_mock = MagicMock(name='user_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserDataService', self.user_ds_mock)

    def test_permission_classes(self):
        self.assertEqual(UserProfileView.permission_classes, (IsAuthenticated, ))

    def test_get_access_and_profile_with_userID(self):
        request_uuid = 'uuid'
        request = MagicMock(name='request', user=self.user_profile.user, data={'userID': request_uuid})
        user_1_profile = MagicMock('user_1_profile')
        user_1_org_access = MagicMock(name='user_1_org_access')
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_1_org_access
        self.user_ds_mock.get_user_profile_by_uuid.return_value = user_1_profile

        access, profile = UserProfileView().get_access_and_profile(request)

        self.assertEqual(access, user_1_org_access)
        self.assertEqual(profile, user_1_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(user_1_profile)
        self.user_ds_mock.get_user_profile_by_uuid.assert_called_once_with(request_uuid)

    def test_get_access_and_profile_without_userID(self):
        request = MagicMock(name='request', user=self.user_profile.user, data={})
        user_org_access = MagicMock(name='user_org_access')
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org_access

        access, profile = UserProfileView().get_access_and_profile(request)

        self.assertEqual(access, user_org_access)
        self.assertEqual(profile, self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)

    def test_post_fails_if_userID_does_not_exist(self):
        request_uuid = 'uuid'
        request = MagicMock(name='request', user=self.user_profile.user, data={'userID': request_uuid})
        get_access_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserProfileView.get_access_and_profile')
        get_access_method_mock.side_effect = UserDoesNotExistError(request_uuid)

        response = UserProfileView().post(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_NOT_EXIST)

    def test_post_fails_if_user_has_no_org(self):
        request_uuid = 'uuid'
        request = MagicMock(name='request', user=self.user_profile.user, data={'userID': request_uuid})
        get_access_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserProfileView.get_access_and_profile')
        get_access_method_mock.side_effect = UserOrgAccessDoesNotExistError(request_uuid)

        response = UserProfileView().post(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error_code'], errors.USER_ORG_MAPPING_NOT_PRESENT)

    def test_post_returns_success(self):
        request_uuid = 'uuid'
        request = MagicMock(name='request', user=self.user_profile.user, data={'userID': request_uuid})
        get_access_method_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserProfileView.get_access_and_profile')
        access = MagicMock(name='access')
        profile = MagicMock(name='profile')
        get_access_method_mock.return_value = (access, profile)

        role_serializer_class_mock = self.patch_class('user_auth.views.user_profile_views.RoleSerializer')
        role_serializer_mock = MagicMock(name='role_serializer_mock', data=1)
        role_serializer_class_mock.return_value = role_serializer_mock

        up_response = {'firstName': 'Bilbo', 'lastName': 'Baggins'}
        up_response_serializer_class_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserProfileResponseSerializer')
        up_response_serializer = MagicMock(name='up_response_serializer', data=up_response)
        up_response_serializer_class_mock.return_value = up_response_serializer

        response = UserProfileView().post(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = {**up_response, 'roles': role_serializer_mock.data}
        self.assertEqual(response.data, expected_response)
        role_serializer_class_mock.assert_called_once_with([access], many=True)
        up_response_serializer_class_mock.assert_called_once_with(profile)
