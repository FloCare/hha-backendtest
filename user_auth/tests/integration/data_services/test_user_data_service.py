from user_auth.data_services import UserDataService
from user_auth.exceptions import *
from user_auth.tests.integration.common import utils
from flocarebase.common.test_helpers import *

import uuid


class TestUserDataService(TestCase):

    def setUp(self):
        self.uds = UserDataService()
        self.organization = create_organization()

    def test_create_user(self):
        """Creates user with requested data"""
        user_data = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'password': 'password',
            'contact_no': 'contact_no',
            'role': 'role'
        }
        self.uds.create_user(user_data, self.organization)
        user = User.objects.first()
        user_profile = UserProfile.objects.first()

        utils.compare_user(self, user, user_data)
        utils.compare_user_profile(self, user_profile, user_data)

        user_org_access = UserOrganizationAccess.objects.first()
        # Validate user org access
        self.assertEqual(user_org_access.user, user_profile)
        self.assertEqual(user_org_access.organization, self.organization)
        self.assertEqual(user_org_access.user_role, user_data['role'])

    def test_create_user_raises_error_user_already_exists(self):
        """ Raises error if user already exists"""
        self.create_user()
        with self.assertRaises(UserAlreadyExistsError):
            self.create_user()

    def test_get_user_profile_by_uuid(self):
        """ Returns requested user profile object """
        self.create_user()
        user_profile = UserProfile.objects.first()
        return_obj = self.uds.get_user_profile_by_uuid(user_profile.uuid)
        self.assertEqual(return_obj, user_profile)

    def test_get_user_profile_by_uuid_raises_error(self):
        """ Raises Error if no user profile exists """
        self.create_user()
        with self.assertRaises(UserDoesNotExistError):
            self.uds.get_user_profile_by_uuid(uuid.uuid4())

    def test_update_user_by_uuid(self):
        """Updates all properties of user and user profile"""
        self.create_user()
        user_profile = UserProfile.objects.first()
        user_data = {
            'first_name': 'new_first_name',
            'last_name': 'new_last_name',
            'email': 'new_email',
            'password': 'new_password',
            'contact_no': 'new_contact_no',
            'role': 'new_role'
        }
        self.uds.update_user_by_uuid(user_profile.uuid, user_data)
        user_profile = UserProfile.objects.first()
        utils.compare_user(self, user_profile.user, user_data)
        utils.compare_user_profile(self, user_profile, user_data)

        user_org_access = UserOrganizationAccess.objects.first()
        # Validate user org access
        self.assertEqual(user_org_access.user, user_profile)
        self.assertEqual(user_org_access.organization, self.organization)
        self.assertEqual(user_org_access.user_role, user_data['role'])

    def test_update_user_by_uuid_raises_error(self):
        """Raises error if user profile with uuid doesn't exist"""
        self.create_user()
        with self.assertRaises(UserDoesNotExistError):
            self.uds.get_user_profile_by_uuid(uuid.uuid4())

    def test_delete_user_by_user_profile(self):
        self.create_user()
        user_profile = UserProfile.objects.first()
        self.uds.delete_user_by_user_profile(user_profile)

        user_profile = UserProfile.all_objects.first()
        self.assertTrue(user_profile.is_deleted)
        self.assertFalse(user_profile.user.is_active)

    def create_user(self):
        user_data = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'email': 'email',
            'password': 'password',
            'contact_no': 'contact_no',
            'role': 'role'
        }
        self.uds.create_user(user_data, self.organization)
