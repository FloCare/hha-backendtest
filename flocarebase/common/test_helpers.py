from django.test import TestCase, Client
from rest_framework.authtoken.models import Token
from user_auth.models import *

import random


class UserRequestTestCase(TestCase):

    @classmethod
    def initObjects(cls):
        cls.organization = create_organization()
        cls.user_profile = create_user(cls.organization)

        Token.objects.create(user=cls.user_profile.user)
        token = Token.objects.all()

        cls.authorization_header = "Token " + token[0].key
        cls.client = Client()

    def get_base_headers(self):
        return {"HTTP_AUTHORIZATION": self.authorization_header}


def create_organization():
    return Organization.objects.create(name='org' + str(random.randint(0, 10000)), type='org', contact_no='234343')


def create_user(organization):
    tag = str(random.randint(0, 10000))
    user = User.objects.create_user(first_name='firstName_' + tag, last_name='lastName_' + tag,
                                    username='username_' + tag, password='password_'+tag, email='email_'+tag)
    user_profile = UserProfile.objects.create(user=user, title='', contact_no='phone_' + tag)
    print('creating user org access for in create user : ' + str(user_profile.uuid))
    UserOrganizationAccess.objects.create(user=user_profile, organization=organization, user_role='user_role')
    return user_profile


def make_user_admin(user_profile):
    UserOrganizationAccess.objects.filter(user=user_profile).update(is_admin=True)
