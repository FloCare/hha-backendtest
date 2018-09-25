from user_auth.serializers import RoleSerializer, UserProfileUpdateSerializer
from user_auth.response_serializers import UserProfileResponseSerializer, AdminUserResponseSerializer, UserDetailsResponseSerializer
from user_auth import models
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from user_auth.constants import query_to_db_field_map
from user_auth.permissions import IsAdminForOrg
from backend import errors
from django.db import transaction
from user_auth.models import Organization, UserProfile, User, Address, UserOrganizationAccess
from phi.views import my_publish_callback
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


# Being used for web API
class UserOrganizationView(APIView):
    """
    Returns the list of users registered with this organization
    """
    permission_classes = (IsAuthenticated, IsAdminForOrg)

    def parse_query_params(self, query_params):
        if not query_params:
            return None, None, None, None
        sort_field = query_params.get('sort', None)
        sort_order = query_params.get('order', 'ASC')
        field_list = models.UserProfile._meta.fields + User._meta.fields
        allowed_fields = map(lambda field: field.name, field_list)
        if sort_field:
            if sort_field not in allowed_fields:
                sort_field = 'first_name'
        else:
            sort_field = 'first_name'
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        try:
            size = int(size)
        except Exception:
            size = None
        return query, sort_field, sort_order, size

    def get_results(self, initial_query_set, query, sort_field, size):
        query_set = initial_query_set
        if query:
            query_set = initial_query_set.filter(Q(user__user__first_name__istartswith=query) | Q(user__user__last_name__istartswith=query))
        if sort_field:
            query_set.order_by(sort_field)
        if size:
            query_set = query_set[:size]
        return query_set

    def get(self, request):
        try:
            user = request.user
            # Get the organization for this user
            user_org = models.UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            org = user_org.organization

            # Todo: Improve Sorting logic - use DRF builtin
            query, sort_field, sort_order, size = self.parse_query_params(request.query_params)
            query_params = request.query_params
            if 'sort' in query_params:
                sort_field = query_to_db_field_map.get(query_params['sort'], sort_field)
                if sort_order == 'DESC':
                    sort_field = '-' + sort_field

            # Get list of all users in that org
            filters = request.GET.getlist('ids')
            print('filters')
            print(filters)
            accesses = models.UserOrganizationAccess.objects.select_related('user', 'user__user').filter(organization=org)
            if filters:
                accesses = accesses.filter(user_id__in=filters)
            accesses = self.get_results(accesses, query, sort_field, size)
            serializer = AdminUserResponseSerializer({'success': True, 'organization': org, 'users': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except UserOrganizationAccess.DoesNotExist as e:
            logger.error(str(e))
            headers = {'Content-Type': 'application/json'}
            return Response({'success': False, 'error': errors.ACCESS_DENIED}, headers=headers)


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
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        try:
            user_org = UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                user_request = request.data.get('user', None)
                if not user_request:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
                try:
                    with transaction.atomic():
                        # Save user to db
                        username = str(user_request['firstName']).strip().lower() + '.' + str(user_request['lastName']).strip().lower()
                        user = User.objects.create_user(first_name=user_request['firstName'], last_name=user_request['lastName'],
                                                        username=user_request['email'], password=user_request['password'], email=user_request['email'])
                        user.save()

                        # Save user profile to db
                        profile = UserProfile(user=user, title='', contact_no=user_request['phone'])
                        profile.save()

                        # Add entry to UserOrganizationAccess: For that org, add all users, and their 'roles'
                        access = UserOrganizationAccess(user=profile, organization=user_org.organization, user_role=user_request['role'])
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
            user_org = UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                user_org1 = UserOrganizationAccess.objects.filter(organization=user_org.organization).get(user_id=pk)
                serializer = UserDetailsResponseSerializer({'user': user_org1})
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def update(self, request, pk=None):
        try:
            user_org = UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
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
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            if user_org:
                user_profile = models.UserProfile.objects.get(uuid=pk)
                user = user_profile.user
                user_org_access = models.UserOrganizationAccess.objects.filter(organization=user_org.organization).get(user=user_profile)
                try:
                    with transaction.atomic():
                        user_profile.delete()
                        user.delete()
                        user_org_access.delete()
                        return Response({'success': True, 'error': None})
                except Exception as e:
                    logger.error(str(e))
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
