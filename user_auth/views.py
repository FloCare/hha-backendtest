from user_auth.serializers import OrganizationSerializer, UserSerializer, UserProfileSerializer, AddressSerializer, UserOrgAccessSerializer, AdminUserResponseSerializer
from user_auth import models
from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = models.Organization.objects.all()
    serializer_class = OrganizationSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = models.Address.objects.all()
    serializer_class = AddressSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = models.UserProfile.objects.all()
    serializer_class = UserProfileSerializer


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
            # Get list of all users in that org
            # Todo: Optimize Queries
            users = models.UserProfile.objects.filter(organizations__id=qs.organization.id).distinct()
            org = models.Organization(id=qs.organization.id)
            serializer = AdminUserResponseSerializer({'success': True, 'organization': org, 'users': users})
            headers = {'Content-Type': 'application/json'}
            return Response(serializer.data, headers=headers)
        except Exception as e:
            print("Error:", e)
            headers = {'Content-Type': 'application/json'}
            return Response({'success': False, 'error': 'Access Denied'}, headers=headers)
