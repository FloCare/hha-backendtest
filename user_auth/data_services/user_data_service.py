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

    def get_user_org_access_by_user_id(self, user_id):
        try:
            return models.UserOrganizationAccess.objects.get(user_id=user_id)
        except models.UserOrganizationAccess.DoesNotExist:
            raise UserDoesNotExistError(user_id)