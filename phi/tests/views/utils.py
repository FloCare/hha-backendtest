from django.test import TestCase, Client
from rest_framework.authtoken.models import Token
from user_auth.models import *


class UserRequestTestCase(TestCase):

    @classmethod
    def initObjects(cls):
        user = User.objects.create_user(first_name='firstName', last_name='lastName', username='username',
                                        password='password', email='email')
        user_profile = UserProfile.objects.create(user=user, title='', contact_no='phone')
        cls.user = user
        cls.user_profile = user_profile
        Token.objects.create(user=user)
        token = Token.objects.all()
        cls.authorization_header = "Token " + token[0].key
        cls.client = Client()

    def getBaseHeaders(self):
        return {"HTTP_AUTHORIZATION": self.authorization_header}
