from backend import errors
from django.conf import settings
from django.db import transaction
from phi.views import my_publish_callback
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth import models
from user_auth.data_services.user_data_service import UserDataService
from user_auth.exceptions import UserAlreadyExistsError, UserDoesNotExistError
from user_auth.serializers.request_serializers import CreateUserRequestSerializer
from user_auth.serializers.response_serializers import UserProfileResponseSerializer, UserDetailsResponseSerializer
from user_auth.serializers.serializers import RoleSerializer, UserProfileUpdateSerializer

import logging

logger = logging.getLogger(__name__)


# Being used by app APIs
class UserProfileView(APIView):
    queryset = models.UserProfile.objects.all()
    serializer_class = UserProfileResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'userID' in data:
            user_id = data['userID']
            try:
                # Get Requested user Profile
                profile = models.UserProfile.objects.get(pk=user_id)
                # Get all orgs for logged in user
                orgs = models.UserOrganizationAccess.objects.filter(user=user.profile).values_list('organization', flat=True)
                # Get if logged-in user has access to requested user profile
                accesses = models.UserOrganizationAccess.objects.filter(organization_id__in=orgs).filter(user=profile)
                return accesses, profile
            except Exception as e:
                logger.error('Error in querying DB: %s' % str(e))
            return None, None
        else:
            profile = user.profile
            try:
                accesses = models.UserOrganizationAccess.objects.filter(user=profile)
                return accesses, profile
            except Exception as e:
                logger.error('Error in querying DB: %s' % str(e))
            return None, None

    def post(self, request):
        try:
            accesses, profile = self.get_results(request)
            if (not accesses) or (not accesses.exists()):
                roles = []
            else:
                serializer = RoleSerializer(accesses, many=True)
                roles = serializer.data
            if not profile:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.USER_NOT_EXIST})
            user_profile_serializer = UserProfileResponseSerializer(profile)
            response = dict(user_profile_serializer.data)
            response.update({'roles': roles})
            return Response(response)
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.UNKNOWN_ERROR})


class UsersViewSet(viewsets.ViewSet):
    queryset = models.User.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request):
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

    def retrieve(self, request, pk=None):
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

    def update(self, request, pk=None):
        try:
            user_org = models.UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                up_obj = models.UserProfile.objects.get(uuid=pk)
                serializer = UserProfileUpdateSerializer(up_obj.user, data=request.data['user'], partial=True)
                serializer.is_valid()
                serializer.save()

                settings.PUBNUB.publish().channel('organisation_' + str(user_org.organization.uuid)).message({
                    'actionType': 'USER_UPDATE',
                    'userID': str(up_obj.uuid)
                }).async(my_publish_callback)

                return Response({'success': True, 'error': None})
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def destroy(self, request, pk=None):
        try:
            user = request.user
            user_org = models.UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            if user_org:
                user_profile = models.UserProfile.objects.get(uuid=pk)
                user = user_profile.user
                try:
                    with transaction.atomic():
                        user_profile.soft_delete()
                        user.is_active = False
                        return Response({'success': True, 'error': None})
                except Exception as e:
                    logger.error(str(e))
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


def user_data_service():
    return UserDataService()
