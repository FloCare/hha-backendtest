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
            user_org = models.UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                user_request = request.data.get('user', None)
                if not user_request:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
                try:
                    with transaction.atomic():
                        # Save user to db
                        user = models.User.objects.create_user(first_name=user_request['firstName'], last_name=user_request['lastName'],
                                                        username=user_request['email'], password=user_request['password'], email=user_request['email'])
                        user.save()

                        # Save user profile to db
                        profile = models.UserProfile(user=user, title='', contact_no=user_request['phone'])
                        profile.save()

                        # Add entry to UserOrganizationAccess: For that org, add all users, and their 'roles'
                        access = models.UserOrganizationAccess(user=profile, organization=user_org.organization, user_role=user_request['role'])
                        access.save()

                        return Response({'success': True, 'error': None})
                except Exception as e:
                    return Response(status=status.HTTP_412_PRECONDITION_FAILED,
                                    data={'success': False, 'error': errors.DATA_INVALID})
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def retrieve(self, request, pk=None):
        # Check if user is admin of this org
        try:
            user_org = models.UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                user_org1 = models.UserOrganizationAccess.objects.filter(organization=user_org.organization).get(user_id=pk)
                serializer = UserDetailsResponseSerializer({'user': user_org1})
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

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