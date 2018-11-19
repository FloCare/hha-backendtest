from backend import errors
from django.db import transaction
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth import models
from user_auth.data_services.user_data_service import UserDataService
from user_auth.exceptions import UserAlreadyExistsError, UserDoesNotExistError
from user_auth.serializers.request_serializers import CreateUserRequestSerializer, UpdateUserRequestSerializer
from user_auth.serializers.response_serializers import UserProfileResponseSerializer, UserDetailsResponseSerializer
from user_auth.serializers.serializers import RoleSerializer
from flocarebase.common.pubnub_service import PubnubService

import logging

logger = logging.getLogger(__name__)


class GetStaffView(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk=None):
        try:
            user_org = models.UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
            if user_org.organization == requested_user_org_access.organization:
                serializer = UserDetailsResponseSerializer({'user': requested_user_org_access})
                return Response(serializer.data)
            else:
                raise UserDoesNotExistError(pk)
        except models.UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except UserDoesNotExistError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})


class UpdateStaffView(APIView):

    permission_classes = (IsAuthenticated,)

    def put(self, request, pk):
        try:
            user_org = models.UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            print(request.data)
            print(pk)
            request_data = request.data.get('user', None)
            if not request_data:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
            requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
            if user_org.organization == requested_user_org_access.organization:
                request_serializer = UpdateUserRequestSerializer(data=request_data)
                if not request_serializer.is_valid():
                    return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
                with transaction.atomic():
                    user_data_service().update_user_by_uuid(pk, request_serializer.validated_data)
                    channel = pub_nub_service().get_organization_channel(user_org.organization)
                    channel = pub_nub_service().get_organization_channel(user_org.organization)
                    user_update_message = pub_nub_service().get_user_update_message(requested_user_org_access.user)
                    pub_nub_service().publish(channel, user_update_message)
                return Response({'success': True, 'error': None})
            else:
                raise UserDoesNotExistError(pk)
        except models.UserOrganizationAccess.DoesNotExist:
            logger.error('User org does not exist')
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except UserDoesNotExistError:
            logger.error('User does not exists for ID: ' + str(pk))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})


class CreateStaffView(APIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user_org = models.UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            user_request = request.data.get('user', None)
            if not user_request:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
            request_serializer = CreateUserRequestSerializer(data=user_request)
            if not request_serializer.is_valid():
                return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
            with transaction.atomic():
                user_data_service().create_user(request_serializer.validated_data, user_org.organization)
                return Response({'success': True, 'error': None})
        except models.UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except UserAlreadyExistsError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_ALREADY_EXISTS})


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
            profile = models.UserProfile.objects.get(pk=user_id)
        else:
            profile = user.profile
        user_org_access = models.UserOrganizationAccess.objects.filter(user=user.profile)
        return user_org_access, profile

    def post(self, request):
        try:
            accesses, profile = self.get_access_and_profile(request)
            serializer = RoleSerializer(accesses, many=True)
            roles = serializer.data
            user_profile_serializer = UserProfileResponseSerializer(profile)
            response = dict(user_profile_serializer.data)
            response.update({'roles': roles})
            return Response(response)
        except models.UserProfile.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.USER_NOT_EXIST})


# Check behaviour before using. Check all cases and message handling
class DeleteStaffView(APIView):
    queryset = models.User.objects.all()
    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk=None):
        try:
            user = request.user
            user_org = models.UserOrganizationAccess.objects.get(user=user.profile, is_admin=True)
            requested_user_org_access = user_data_service().get_user_org_access_by_user_id(pk)
            if user_org.organization == requested_user_org_access.organization:
                user_profile = requested_user_org_access.user
                with transaction.atomic():
                    user_data_service().delete_user_by_user_profile(user_profile)
                    return Response({'success': True, 'error': None})
            else:
                raise UserDoesNotExistError(pk)
        except models.UserOrganizationAccess.DoesNotExist:
            logger.error('User org does not exist')
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except UserDoesNotExistError:
            logger.error('User does not exists for ID: ' + str(pk))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})


def user_data_service():
    return UserDataService()


def pub_nub_service():
    return PubnubService()
