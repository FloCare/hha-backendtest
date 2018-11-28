from django.urls import reverse
from flocarebase.common import test_helpers
from rest_framework import status
from unittest.mock import patch

import uuid
import logging

logger = logging.getLogger(__name__)


class TestGetStaffView(test_helpers.UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def setUp(self):
        user_org_ds_patcher = patch('user_auth.data_services.UserOrgAccessDataService')
        logger.info('setting up')
        self.user_org_ds_patch = user_org_ds_patcher.start()
        self.addCleanup(user_org_ds_patcher.stop)
        logger.info('setting upd done')

    def test_validates_admin_checks(self):
        # TODO mock user org access everywhere including permissions
        url = reverse('get-staff', args=[uuid.uuid4()])
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_raises_error(self):
        """Raises 400 if requested user is not from the same organization"""
        test_helpers.make_user_admin(self.user_profile)

        org = test_helpers.create_organization()
        user_profile = test_helpers.create_user(org)

        url = reverse('get-staff', args=[user_profile.uuid])
        response = self.client.get(url, **self.get_base_headers())

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        logger.info(response.body)

