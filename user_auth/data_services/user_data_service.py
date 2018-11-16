from user_auth import models
from django.db import IntegrityError
from django.db.models import Q
from user_auth.exceptions import UserAlreadyExistsError, UserDoesNotExistError
import logging

logger = logging.getLogger(__name__)


class UserDataService:

    def create_user(self, user_data, organization):
        try:
            user = models.User.objects.create_user(first_name=user_data['first_name'], last_name=user_data['last_name'],
                                                   username=user_data['email'], password=user_data['password'],
                                                   email=user_data['email'])
            user.save()

            # Save user profile to db
            profile = models.UserProfile(user=user, title='', contact_no=user_data['contact_no'])
            profile.save()

            # Add entry to UserOrganizationAccess: For that org, add all users, and their 'roles'
            access = models.UserOrganizationAccess(user=profile, organization=organization,user_role=user_data['role'])
            access.save()
        except IntegrityError as e:
            # TODO Make it more specific
            logger.error(e)
            raise UserAlreadyExistsError(user_data)

    def get_user_org_access_by_user_id(self, user_id):
        try:
            return models.UserOrganizationAccess.objects.get(user_id=user_id)
        except models.UserOrganizationAccess.DoesNotExist:
            raise UserDoesNotExistError(user_id)

    def get_user_org_access_for_org(self, organization, select_related_fields):
        return models.UserOrganizationAccess.objects.select_related(*select_related_fields).filter(organization=organization)

    def filter_org_access_by_user_ids(self, accesses, user_ids):
        return accesses.filter(user_id__in=user_ids)

    def filter_acccesses_by_name(self, accesses, query):
        return accesses.filter(Q(user__user__first_name__istartswith=query) | Q(user__user__last_name__istartswith=query))

    def update_user_by_uuid(self, uuid, user_data):
        user_profile = models.UserProfile.objects.get(uuid=uuid)
        user = user_profile.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        new_password = user_data.get('password')
        if new_password:
            user.set_password(new_password)
        user.email = user_data.get('email', user.email)
        user.username = user_data.get('email', user.username)
        user.save()

        user_profile.contact_no = user_data.get('contact_no', user_profile.contact_no)
        user_profile.save()

        user_org_access = models.UserOrganizationAccess.objects.get(user=user_profile)
        user_org_access.user_role = user_data.get('role', user_org_access.user_role)
        user_org_access.save()

    def delete_user_by_user_profile(self, user_profile):
        user_profile.soft_delete()
        user = user_profile.user
        user.is_active = False
        user.save()