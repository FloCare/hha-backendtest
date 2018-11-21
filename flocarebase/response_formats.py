from rest_framework.response import Response
from rest_framework import status as http_status

UNKNOWN_ERROR = 'UNKNOWN_ERROR'
NO_ERROR_MESSAGE = 'NO_ERROR_MESSAGE'


class SuccessResponse(Response):
    def __init__(self, status=http_status.HTTP_200_OK, data=None):
        super().__init__(status=status, data=data)


class FailureResponse(Response):
    def __init__(self, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR, code=UNKNOWN_ERROR, message=NO_ERROR_MESSAGE,
                 data=None):
        response_body = {
            'code': code,
            'message': message,
            'data': data
        }
        super().__init__(status=status, data=response_body)
