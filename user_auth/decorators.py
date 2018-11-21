from backend import errors
from flocarebase.exceptions import InvalidPayloadError
from flocarebase.response_formats import FailureResponse
from rest_framework import status
from user_auth.exceptions import UserOrgAccessDoesNotExistError, UserDoesNotExistError

import logging

logger = logging.getLogger(__name__)


def handle_request_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidPayloadError as e:
            logger.error(str(e))
            return FailureResponse(status=status.HTTP_400_BAD_REQUEST, code=errors.DATA_INVALID, message=str(e))
    return wrapper


def handle_user_org_missing(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserOrgAccessDoesNotExistError as e:
            logger.error(str(e))
            return FailureResponse(status=status.HTTP_400_BAD_REQUEST, code=errors.USER_ORG_MAPPING_NOT_PRESENT, message=str(e))
    return wrapper


def handle_user_missing(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserDoesNotExistError as e:
            logger.error(str(e))
            return FailureResponse(status=status.HTTP_400_BAD_REQUEST, code=errors.USER_NOT_EXIST, message=str(e))
    return wrapper
