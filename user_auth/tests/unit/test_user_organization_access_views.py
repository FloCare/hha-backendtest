from rest_framework import status
from rest_framework.test import APIRequestFactory
from flocarebase.common import test_helpers
from django.urls import reverse
from unittest.mock import MagicMock
from user_auth.views.user_organization_access_views import UserOrganizationView
from user_auth.constants import query_to_db_field_map
import logging

logger = logging.getLogger(__name__)


class TestUserOrganizationView(test_helpers.BaseTestCase):

    def setUp(self):
        self.org = test_helpers.create_organization()
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_organization_access_views.UserOrgAccessDataService', self.user_org_access_ds_mock)

    def test_parse_query_params_default_param(self):
        """Returns sort field as first_name if not recognised"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'sort': 'bla'})
        self.assertEqual(sort_field, query_to_db_field_map['first_name'])
        self.assertIsNone(query)
        self.assertIsNone(size)

    def test_parse_query_params_sort_field(self):
        """Returns sort field if passed and valid"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'sort': 'last_name'})
        self.assertEqual(sort_field, query_to_db_field_map['last_name'])
        self.assertIsNone(query)
        self.assertIsNone(size)

    def test_sort_order_default(self):
        """Returns asc order by default"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'sort': 'first_name', 'order': 'BLA'})
        expected_sort_field = query_to_db_field_map['first_name']
        self.assertEqual(sort_field, expected_sort_field)
        self.assertIsNone(query)
        self.assertIsNone(size)

    def test_sort_order_desc(self):
        """Returns negative sort field if order is DESC"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'sort': 'first_name', 'order': 'DESC'})
        expected_sort_field = '-' + query_to_db_field_map['first_name']
        self.assertEqual(sort_field, expected_sort_field)
        self.assertIsNone(query)
        self.assertIsNone(size)

    def test_size(self):
        """Returns size if parameter is passed"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'size': 30})
        self.assertEqual(size, 30)
        self.assertEqual(sort_field, query_to_db_field_map['first_name'])
        self.assertIsNone(query)

    def test_query(self):
        """Returns query if parameter is passed"""
        query, sort_field, size = UserOrganizationView().parse_query_params({'query': 'yoohoo'})
        self.assertIsNone(size)
        self.assertEqual(sort_field, query_to_db_field_map['first_name'])
        self.assertEqual(query, 'yoohoo')

    def test_filter_by_params_with_ids(self):
        """Filters accesses if ids are passed"""
        user_ids = [1,2]

        select_related_fields = ('user', 'user__user')
        base_access = MagicMock(name='base_access')
        filtered_user_id_access = MagicMock(name='filtered_user_id_access')
        self.user_org_access_ds_mock.get_user_org_access_for_org.return_value = base_access
        self.user_org_access_ds_mock.filter_org_access_by_user_ids.return_value = filtered_user_id_access

        query_set = UserOrganizationView().filter_by_params(user_ids, self.org, None, None, None)

        self.user_org_access_ds_mock.get_user_org_access_for_org.assert_called_once_with(self.org, select_related_fields)
        self.user_org_access_ds_mock.filter_org_access_by_user_ids.assert_called_once_with(base_access, user_ids)
        self.assertEqual(query_set, filtered_user_id_access)

    def test_filter_by_params_with_query(self):
        query = 'query'
        select_related_fields = ('user', 'user__user')

        base_access = MagicMock(name='base_access')
        query_filtered_access = MagicMock(name='query_filtered_access')

        self.user_org_access_ds_mock.get_user_org_access_for_org.return_value = base_access
        self.user_org_access_ds_mock.filter_acccesses_by_name.return_value = query_filtered_access

        query_set = UserOrganizationView().filter_by_params(None, self.org, query, None, None)

        self.user_org_access_ds_mock.get_user_org_access_for_org.assert_called_once_with(self.org,select_related_fields)
        self.user_org_access_ds_mock.filter_acccesses_by_name.assert_called_once_with(base_access, query)

        self.assertEqual(query_set, query_filtered_access)

    def test_filter_by_params_with_sort_field(self):
        sort_field = 'sort_field'
        select_related_fields = ('user', 'user__user')

        base_access = MagicMock(name='base_access')
        ordered_access = MagicMock(name='ordered_access')

        self.user_org_access_ds_mock.get_user_org_access_for_org.return_value = base_access
        base_access.order_by.return_value = ordered_access

        query_set = UserOrganizationView().filter_by_params(None, self.org, None, sort_field, None)

        self.user_org_access_ds_mock.get_user_org_access_for_org.assert_called_once_with(self.org,select_related_fields)
        base_access.order_by.assert_called_once_with(sort_field)

        self.assertEqual(query_set, ordered_access)

    # TODO Add test for size filter


class TestUserOrganizationViewAPI(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.initObjects()

    def setUp(self):
        self.user_org_access_ds_mock = MagicMock(name='user_org_access_ds_mock')
        self.patch_class('user_auth.views.user_organization_access_views.UserOrgAccessDataService',
                         self.user_org_access_ds_mock)
        self.admin_user_resp_serializer_mock = MagicMock(name='admin_user_resp_serializer_mock')
        self.admin_user_response_ser_class = self.patch_class(
            'user_auth.views.user_organization_access_views.AdminUserResponseSerializer',
            self.admin_user_resp_serializer_mock)

    def test_checks_admin(self):
        url = reverse('org-access')
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_response_for_simple(self):
        url = reverse('org-access')
        test_helpers.make_user_admin(self.user_profile)

        user_org_mock = MagicMock(name='user_org_mock', organization=self.organization)
        base_accesses = MagicMock(name='base_accesses')
        ordered_accesses = MagicMock(name='ordered_accesses')
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.return_value = user_org_mock
        self.user_org_access_ds_mock.get_user_org_access_for_org.return_value = base_accesses
        base_accesses.order_by.return_value = ordered_accesses
        self.admin_user_resp_serializer_mock.data = 1
        response = self.client.get(url, **self.get_base_headers())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user_org_access_ds_mock.get_user_org_access_by_user_profile.assert_called_once_with(self.user_profile)
        select_related_fields = ('user', 'user__user')
        self.user_org_access_ds_mock.get_user_org_access_for_org.assert_called_once_with(self.organization,
                                                                                         select_related_fields)
        base_accesses.order_by.assert_called_once_with(query_to_db_field_map['first_name'])
        self.admin_user_response_ser_class.assert_called_once_with({'organization': self.organization,
                                                                    'users': ordered_accesses})
        self.assertEqual(response.data, self.admin_user_resp_serializer_mock.data)
