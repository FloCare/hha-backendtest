from user_auth.serializers import AdminUserResponseSerializer, UserProfileForAppSerializer
from user_auth import models
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user_auth.constants import query_to_db_field_map
from user_auth.permissions import IsAdminForOrg
from backend import errors
import logging

logger = logging.getLogger(__name__)


# Being used for web API
class UserOrganizationView(APIView):
    """
    Returns the list of users registered with this organization
    """
    permission_classes = (IsAuthenticated, IsAdminForOrg)

    def get(self, request):
        try:
            user = request.user
            # Get the organization for this user
            qs = models.UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            org = qs.organization

            # Todo: Improve Sorting logic - use DRF builtin
            query_params = request.query_params
            sort_field = 'user__user__first_name'
            order = 'ASC'
            if 'sort' in query_params:
                sort_field = query_to_db_field_map.get(query_params['sort'], sort_field)
                if 'order' in query_params:
                    order = query_params['order']
            if order == 'DESC':
                sort_field = '-' + sort_field

            # Get list of all users in that org
            filters = request.query_params.get('ids', None)
            accesses = models.UserOrganizationAccess.objects.filter(organization=org).order_by(sort_field)
            # TODO: Don't use eval
            if filters:
                try:
                    filters = list(eval(filters))
                except Exception as e:
                    logger.warning('Filters not a list: %s' % str(e))
                    filters = [filters]
                accesses = accesses.filter(user_id__in=filters)
            serializer = AdminUserResponseSerializer({'success': True, 'organization': org, 'users': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except Exception as e:
            logger.error(str(e))
            headers = {'Content-Type': 'application/json'}
            return Response({'success': False, 'error': errors.ACCESS_DENIED}, headers=headers)


# Being used by app API
class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        try:
            profile = user.profile
            accesses = models.UserOrganizationAccess.objects.filter(user=profile)
            serializer = UserProfileForAppSerializer({'id': profile.uuid, 'roles': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.UNKNOWN_ERROR})
