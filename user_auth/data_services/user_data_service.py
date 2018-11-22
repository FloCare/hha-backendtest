from user_auth import models
from django.db import IntegrityError
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

    def get_user_profile_by_uuid(self, user_id):
        try:
            return models.UserProfile.objects.get(pk=user_id)
        except models.UserProfile.DoesNotExist:
            raise UserDoesNotExistError(user_id)

    def update_user_by_uuid(self, uuid, user_data):
        try:
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
        except models.UserProfile.DoesNotExist:
            raise UserDoesNotExistError(uuid)

    def delete_user_by_user_profile(self, user_profile):
        user_profile.soft_delete()
        user = user_profile.user
        user.is_active = False
        user.save()