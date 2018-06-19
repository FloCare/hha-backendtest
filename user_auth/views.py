from user_auth.serializers import AdminUserResponseSerializer, UserProfileForAppSerializer
from user_auth import models
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


# Being used for web API
class UserOrganizationView(APIView):
    """
    Returns the list of users registered with this organization
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        try:
            user = request.user
            # Check if this user is admin
            qs = models.UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            org = qs.organization

            # Get list of all users in that org
            filters = request.query_params.get('ids', None)
            accesses = models.UserOrganizationAccess.objects.filter(organization_id=org.id)
            # TODO: Don't use eval
            if filters:
                try:
                    filters = list(eval(filters))
                except Exception as e:
                    print('Error. Filters not a list:', str(e))
                    filters = [int(filters)]
                accesses = accesses.filter(user_id__in=filters)
            serializer = AdminUserResponseSerializer({'success': True, 'organization': org, 'users': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except Exception as e:
            print("Error:", e)
            headers = {'Content-Type': 'application/json'}
            return Response({'success': False, 'error': 'Access Denied'}, headers=headers)


# Being used by app API
class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        user = request.user

        try:
            user_id = user.profile.id
            accesses = models.UserOrganizationAccess.objects.filter(user_id=user_id)
            serializer = UserProfileForAppSerializer({'id': user_id, 'roles': accesses})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except Exception as e:
            print('Error:', str(e))
            return Response(status=400, data={'error': 'Something went wrong'})
