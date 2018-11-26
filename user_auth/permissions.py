from rest_framework import permissions
from user_auth.data_services import UserOrgAccessDataService
from user_auth.exceptions import UserOrgAccessDoesNotExistError

import logging

logger = logging.getLogger(__name__)


class IsAdminForOrg(permissions.BasePermission):
    """
    Permission class to allow only admin users access data
    """
    message = "Admin access needed"

    def has_permission(self, request, view):
        try:
            user_org = user_org_access_data_service().get_user_org_access_by_user_profile(request.user.profile)
            return (user_org is not None) and user_org.is_admin
        except UserOrgAccessDoesNotExistError:
            logger.error('User org access does not exist for user')
            return False


def user_org_access_data_service():
    return UserOrgAccessDataService()
