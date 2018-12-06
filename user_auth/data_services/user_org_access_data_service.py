from user_auth import models
from django.db.models import Q
from user_auth.exceptions import UserOrgAccessDoesNotExistError
import logging

logger = logging.getLogger(__name__)


class UserOrgAccessDataService:

    @staticmethod
    def get_user_org_access_by_user_id(user_id):
        try:
            return models.UserOrganizationAccess.objects.get(user_id=user_id)
        except models.UserOrganizationAccess.DoesNotExist:
            raise UserOrgAccessDoesNotExistError(user_id)

    @staticmethod
    def get_user_org_access_by_user_profile(user_profile):
        try:
            return models.UserOrganizationAccess.objects.get(user=user_profile)
        except models.UserOrganizationAccess.DoesNotExist:
            raise UserOrgAccessDoesNotExistError(user_profile.uuid)

    @staticmethod
    def get_user_org_access_for_org(organization, select_related_fields):
        return models.UserOrganizationAccess.objects.select_related(*select_related_fields).filter(organization=organization)

    @staticmethod
    def filter_org_access_by_user_ids(accesses, user_ids):
        return accesses.filter(user_id__in=user_ids)

    @staticmethod
    def filter_accesses_by_name(accesses, query):
        return accesses.filter(Q(user__user__first_name__istartswith=query) | Q(user__user__last_name__istartswith=query))

