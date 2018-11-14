from backend import errors
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth import models
from user_auth.constants import query_to_db_field_map
from user_auth.permissions import IsAdminForOrg
from user_auth.serializers.response_serializers import AdminUserResponseSerializer

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
            accesses = models.UserOrganizationAccess.objects.select_related('user', 'user__user').filter(organization=org)
            if filters:
                accesses = accesses.filter(user_id__in=filters)
            accesses = self.get_results(accesses, query, sort_field, size)
            serializer = AdminUserResponseSerializer({'success': True, 'organization': org, 'users': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except models.UserOrganizationAccess.DoesNotExist as e:
            logger.error(str(e))
            headers = {'Content-Type': 'application/json'}
            return Response({'success': False, 'error': errors.ACCESS_DENIED}, headers=headers)