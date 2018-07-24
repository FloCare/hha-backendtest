from rest_framework import serializers
from user_auth import models


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    zipCode = serializers.CharField(source='zip')
    streetAddress = serializers.CharField(source='street_address')
    apartmentNo = serializers.CharField(source='apartment_no')

    class Meta:
        model = models.Address
        fields = ('id', 'apartmentNo', 'streetAddress', 'zipCode', 'city', 'state', 'country', 'latitude', 'longitude',)

    def create(self, validated_data):
        """
        Create and return a new Address instance, given the validated data
        :param validated_data:
        :return:
        """
        return models.Address.objects.create(**validated_data)


class OrganizationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')

    class Meta:
        model = models.Organization
        fields = ('id', 'name', 'type', 'contact_no', 'address')


class RoleSerializer(serializers.ModelSerializer):
    org = serializers.CharField(source='organization.name')
    role = serializers.CharField(source='user_role')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('org', 'role')


class UserProfileForAppSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    roles = RoleSerializer(many=True)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    class Meta:
        fields = ('id', 'roles')


class UserProfileWithOrgAccessSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='user.uuid')
    old_id = serializers.IntegerField(source='user.id')
    first_name = serializers.CharField(source='user.user.first_name')
    last_name = serializers.CharField(source='user.user.last_name')
    username = serializers.CharField(source='user.user.username')
    email = serializers.CharField(source='user.user.email')
    title = serializers.CharField(source='user.title')
    contact_no = serializers.CharField(source='user.contact_no')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('id', 'old_id', 'title', 'first_name', 'last_name', 'username', 'contact_no', 'email', 'user_role')


class AdminUserResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    organization = OrganizationSerializer()
    users = UserProfileWithOrgAccessSerializer(many=True)

    class Meta:
        fields = ('success', 'organization', 'users',)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class UserProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    username = serializers.CharField(source='user.username')
    contactNo = serializers.CharField(source='contact_no')

    class Meta:
        model = models.UserProfile
        fields = ('id', 'firstName', 'lastName', 'username', 'contactNo', 'address')
