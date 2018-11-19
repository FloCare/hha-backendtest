from backend import errors
from flocarebase.exceptions import InvalidPayloadError
from rest_framework import status
from rest_framework.response import Response
from user_auth.exceptions import UserOrgAccessDoesNotExistError, UserDoesNotExistError

import logging

logger = logging.getLogger(__name__)


def handle_request_execptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidPayloadError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': e.message})
    return wrapper


def handle_user_org_missing(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserOrgAccessDoesNotExistError as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False,
                                                                      'error': errors.USER_ORG_MAPPING_NOT_PRESENT})
    return wrapper


def handle_user_missing(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserDoesNotExistError as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})
    return wrapper
