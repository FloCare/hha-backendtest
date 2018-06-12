from rest_framework import serializers
from user_auth import models
from django.contrib.auth.models import User


class AddressSerializer(serializers.ModelSerializer):
    zipCode = serializers.CharField(source='zip')
    streetAddress = serializers.CharField(source='street_address')

    class Meta:
        model = models.Address
        fields = ('id', 'apartment_no', 'streetAddress', 'zipCode', 'city', 'state', 'country', 'latitude', 'longitude',)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    username = serializers.CharField(source='user.username')
    email = serializers.CharField(source='user.email')
    is_admin = serializers.BooleanField(source='user.is_superuser', read_only=True)

    class Meta:
        model = models.UserProfile
        fields = ('id', 'title', 'first_name', 'last_name', 'username', 'email', 'contact_no', 'qualification', 'address', 'is_admin')   # noqa


class UserSerializer(serializers.ModelSerializer):
    contact_no = serializers.CharField(source='profile.contact_no', read_only=True)
    title = serializers.CharField(source='profile.title', read_only=True)
    is_admin = serializers.BooleanField(source='is_superuser', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'title', 'first_name', 'last_name', 'username', 'email', 'contact_no', 'is_admin')


class UserOrganizationAccessSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer()
    user = UserProfileSerializer()

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('id', 'organization', 'user', 'user_role', 'is_admin',)
