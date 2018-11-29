from rest_framework import status
from flocarebase.common import test_helpers
from django.urls import reverse
from unittest.mock import MagicMock
import logging
import uuid

logger = logging.getLogger(__name__)


class TestGetStaffViewAPI(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_profile_views.UserOrgAccessDataService', self.user_org_access_ds_mock)

    def test_checks_admin(self):
        url = reverse('get-staff', args=[uuid.uuid4()])
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validates_same_org(self):
        test_helpers.make_user_admin(self.user_profile)
        user_oa_mock = MagicMock(name='user_org_mock', organization = self.organization)
        org_1 = test_helpers.create_organization()
        user_1_uuid = uuid.uuid4()
        user_1_oa_mock = MagicMock(name='user_1_org_access', organization=org_1)
        url = reverse('get-staff', args=[user_1_uuid])
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_oa_mock
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_oa_mock

        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1_uuid)

    def test_returns_staff_data(self):
        test_helpers.make_user_admin(self.user_profile)
        user_oa_mock = MagicMock(name='user_org_mock', organization=self.organization)
        user_1 = test_helpers.create_user(self.organization)
        user_1_oa_mock = MagicMock(name='user_1_org_access', organization=self.organization)
        url = reverse('get-staff', args=[user_1.uuid])
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_oa_mock
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.return_value = user_1_oa_mock

        user_details_ser_mock = MagicMock(name='user_details_ser_mock')
        user_details_ser_class_mock = self.patch_class(
            'user_auth.views.user_profile_views.UserDetailsResponseSerializer', user_details_ser_mock)
        serializer_mock = MagicMock(name='serializer_mock', data=1)
        user_details_ser_class_mock.return_value = serializer_mock
        response = self.client.get(url, **self.get_base_headers())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        self.user_org_access_ds_mock.get_user_org_access_by_user_id.assert_called_once_with(user_1.uuid)
        user_details_ser_class_mock.assert_called_once_with({'user': user_1_oa_mock})
        self.assertEqual(response.data, serializer_mock.data)