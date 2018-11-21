from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.views import APIView
from user_auth.constants import query_to_db_field_map
from user_auth.data_services import UserDataService, UserOrgAccessDataService
from user_auth.decorators import handle_user_org_missing
from user_auth.permissions import IsAdminForOrg
from flocarebase.response_formats import SuccessResponse, FailureResponse
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
        sort_field = query_params.get('sort', 'first_name')
        sort_order = query_params.get('order', 'ASC')
        sort_field = query_to_db_field_map.get(sort_field)
        if sort_order == 'DESC':
            sort_field = '-' + sort_field
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        size = int(size) if size else None
        return query, sort_field, size

    def filter_by_params(self, user_ids, org, query, sort_field, size):
        accesses = user_org_access_data_service().get_user_org_access_for_org(org, ('user', 'user__user'))
        if user_ids:
            accesses = user_org_access_data_service().filter_org_access_by_user_ids(accesses, user_ids)
        query_set = accesses
        if query:
            query_set = user_org_access_data_service().filter_acccesses_by_name(accesses, query)
        if sort_field:
            query_set = query_set.order_by(sort_field)
        if size:
            query_set = query_set[:size]
        return query_set

    @handle_user_org_missing
    def get(self, request):
        user_org = user_org_access_data_service().get_user_org_access_by_user_profile(request.user.profile)
        organization = user_org.organization
        query, sort_field, size = self.parse_query_params(request.query_params)

        # Get list of all users in that org
        user_ids = request.GET.getlist('ids')
        accesses = self.filter_by_params(user_ids, organization, query, sort_field, size)
        # TODO Remove organization - why is org required?
        serializer = AdminUserResponseSerializer({'success': True, 'organization': organization, 'users': accesses})
        return SuccessResponse(status.HTTP_200_OK, serializer.data)


def user_data_service():
    return UserDataService()


def user_org_access_data_service():
    return UserOrgAccessDataService()
