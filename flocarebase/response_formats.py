from rest_framework.response import Response
from rest_framework import status as http_status
from backend import errors
DEFAULT_ERROR_MESSAGE = 'Something went wrong'


class SuccessResponse(Response):
    def __init__(self, status=http_status.HTTP_200_OK, data=None):
        super().__init__(status=status, data=data)


class FailureResponse(Response):
    def __init__(self, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR, code=errors.UNKNOWN_ERROR,
                 message=DEFAULT_ERROR_MESSAGE, data=None):
        response_body = {
            'error_code': code,
            'error_message': message,
            'data': data
        }
        super().__init__(status=status, data=response_body)
