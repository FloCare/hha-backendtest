from user_auth.serializers import OrganizationSerializer, UserSerializer, UserProfileSerializer, AddressSerializer, UserOrganizationAccessSerializer
from user_auth import models
from rest_framework import viewsets
from django.contrib.auth.models import User


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


class UserOrganizationViewSet(viewsets.ModelViewSet):
    queryset = models.UserOrganizationAccess.objects.all()
    serializer_class = UserOrganizationAccessSerializer
