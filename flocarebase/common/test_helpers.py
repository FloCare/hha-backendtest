import random
from user_auth.models import *


def create_organization():
    return Organization.objects.create(name='org' + str(random.randint(0, 10000)), type='org', contact_no='234343')