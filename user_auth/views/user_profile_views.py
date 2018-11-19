from backend import errors
from django.db import transaction
from flocarebase.exceptions import InvalidPayloadError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth import models
from user_auth.data_services.user_data_service import UserDataService
from user_auth.decorators import handle_request_execptions, handle_user_missing, handle_user_org_missing
from user_auth.exceptions import UserAlreadyExistsError, UserDoesNotExistError, UserOrgAccessDoesNotExistError
from user_auth.permissions import IsAdminForOrg
from user_auth.serializers.request_serializers import CreateUserRequestSerializer, UpdateUserRequestSerializer
from user_auth.serializers.response_serializers import UserProfileResponseSerializer, UserDetailsResponseSerializer
from user_auth.serializers.serializers import RoleSerializer
from flocarebase.common.pubnub_service import PubnubService

import logging

logger = logging.getLogger(__name__)


class GetStaffView(APIView):

    permission_classes = (IsAuthenticated, IsAdminForOrg)

    @handle_user_org_missing
    @handle_user_missing
    def get(self, request, pk=None):
        try:
            user_org = user_data_service().get_user_org_access_by_user_profile(request.user.profile)
        except UserOrgAccessDoesNotExistError:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False,
                                                                       'error': errors.USER_ORG_MAPPING_NOT_PRESENT})
        requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
        if user_org.organization != requested_user_org_access.organization:
            raise UserDoesNotExistError(pk)
        serializer = UserDetailsResponseSerializer({'user': requested_user_org_access})
        return Response(serializer.data)


class UpdateStaffView(APIView):

    permission_classes = (IsAuthenticated, IsAdminForOrg)

    def validate_and_format_request(self, request):
        request_data = request.data.get('user', None)
        if not request_data:
            raise InvalidPayloadError('user data missing')
        request_serializer = UpdateUserRequestSerializer(data=request_data)
        if not request_serializer.is_valid():
            raise InvalidPayloadError(request_serializer.errors)
        return request_serializer.validated_data

    @handle_request_execptions
    @handle_user_org_missing
    @handle_user_missing
    def put(self, request, pk):
        try:
            user_org = user_data_service().get_user_org_access_by_user_profile(request.user.profile)
        except UserOrgAccessDoesNotExistError:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'success': False, 'error': errors.USER_ORG_MAPPING_NOT_PRESENT})
        formatted_request_data = self.validate_and_format_request(request)
        requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
        if user_org.organization != requested_user_org_access.organization:
            raise UserDoesNotExistError(pk)
        with transaction.atomic():
            user_data_service().update_user_by_uuid(pk, formatted_request_data)
            channel = pub_nub_service().get_organization_channel(user_org.organization)
            user_update_message = pub_nub_service().get_user_update_message(requested_user_org_access.user)
            pub_nub_service().publish(channel, user_update_message)
        return Response({'success': True, 'error': None})


class CreateStaffView(APIView):

    permission_classes = (IsAuthenticated, IsAdminForOrg)

    def validate_and_format_request(self, request):
        user_request = request.data.get('user', None)
        if not user_request:
            raise InvalidPayloadError('user data missing')
        request_serializer = CreateUserRequestSerializer(data=user_request)
        if not request_serializer.is_valid():
            raise InvalidPayloadError(request_serializer.errors)
        return request_serializer.validated_data

    @handle_request_execptions
    def post(self, request):
        try:
            try:
                user_org = user_data_service().get_user_org_access_by_user_profile(request.user.profile)
            except UserOrgAccessDoesNotExistError:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False,
                                                                           'error': errors.USER_ORG_MAPPING_NOT_PRESENT})
            formatted_request_data = self.validate_and_format_request(request)
            with transaction.atomic():
                user_data_service().create_user(formatted_request_data, user_org.organization)
                return Response({'success': True, 'error': None})
        except UserAlreadyExistsError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False,
                                                                      'error': errors.USER_ALREADY_EXISTS})


# Check behaviour before using. Check all cases and message handling
class DeleteStaffView(APIView):

    permission_classes = (IsAuthenticated, IsAdminForOrg)

    @handle_user_org_missing
    @handle_user_missing
    def delete(self, request, pk=None):
        try:
            user_org = user_data_service().get_user_org_access_by_user_profile(request.user.profile)
        except UserOrgAccessDoesNotExistError:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'success': False, 'error': errors.USER_ORG_MAPPING_NOT_PRESENT})

        requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
        if user_org.organization != requested_user_org_access.organization:
            raise UserDoesNotExistError(pk)
        requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
        if user_org.organization != requested_user_org_access.organization:
            raise UserDoesNotExistError(pk)
        user_profile = requested_user_org_access.user
        with transaction.atomic():
            user_data_service().delete_user_by_user_profile(user_profile)
            return Response({'success': True, 'error': None})


# Being used by app APIs
class UserProfileView(APIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = UserProfileResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_access_and_profile(self, request):
        user = request.user
        data = request.data
        if 'userID' in data:
            user_id = data['userID']
            profile = user_data_service().get_user_profile_by_uuid(user_id)
        else:
            profile = user.profile
        user_org_access = user_data_service().get_user_org_access_by_user_profile(profile)
        return user_org_access, profile

    @handle_user_org_missing
    @handle_user_missing
    def post(self, request):
        accesses, profile = self.get_access_and_profile(request)
        serializer = RoleSerializer(accesses, many=True)
        roles = serializer.data
        user_profile_serializer = UserProfileResponseSerializer(profile)
        response = dict(user_profile_serializer.data)
        response.update({'roles': roles})
        return Response(response)


def user_data_service():
    return UserDataService()


def pub_nub_service():
    return PubnubService()
