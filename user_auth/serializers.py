from rest_framework import serializers
from user_auth import models


class AddressSerializer(serializers.ModelSerializer):
    addressID = serializers.UUIDField(source='uuid', required=False)
    zipCode = serializers.CharField(source='zip', required=False)
    streetAddress = serializers.CharField(source='street_address', required=False)
    apartmentNo = serializers.CharField(source='apartment_no', required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    country = serializers.CharField(required=False)

    class Meta:
        model = models.Address
        fields = ('addressID', 'apartmentNo', 'streetAddress', 'zipCode', 'city', 'state', 'country', 'latitude', 'longitude',)

    def create(self, validated_data):
        """
        Create and return a new Address instance, given the validated data
        :param validated_data:
        :return:
        """
        return models.Address.objects.create(**validated_data)


class RoleSerializer(serializers.ModelSerializer):
    org = serializers.CharField(source='organization.name')
    role = serializers.CharField(source='user_role')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('org', 'role')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('first_name', 'last_name', 'email')


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    phone = serializers.CharField(source='contact_no', required=False)
    firstName = serializers.CharField(source='first_name', required=False)
    lastName = serializers.CharField(source='last_name', required=False)
    password = serializers.CharField(required=False)
    role = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = models.UserProfile
        fields = ('id', 'phone', 'firstName', 'lastName', 'password', 'role', 'email', 'is_active')

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.set_password(instance.password)
        instance.email = validated_data.get('email', instance.email)
        instance.username = validated_data.get('email', instance.username)
        instance.save()

        user_profile = models.UserProfile.objects.get(user=instance)
        user_profile.contact_no = validated_data.get('contact_no', user_profile.contact_no)
        user_profile.save()

        user_org_access = models.UserOrganizationAccess.objects.get(user=user_profile)
        user_org_access.user_role = validated_data.get('role', user_org_access.user_role)
        user_org_access.is_active = validated_data.get('is_active', user_org_access.is_active)
        user_org_access.save()
        return instance
