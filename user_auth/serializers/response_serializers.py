from rest_framework import serializers
from user_auth import models


class UserProfileResponseSerializer(serializers.ModelSerializer):
    userID = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    username = serializers.CharField(source='user.username')
    primaryContact = serializers.CharField(source='contact_no')
    addressID = serializers.UUIDField(source='address_id')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = models.UserProfile
        fields = ('userID', 'firstName', 'lastName', 'username', 'primaryContact', 'addressID', 'email')


class OrganizationSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')

    class Meta:
        model = models.Organization
        fields = ('id', 'name', 'type', 'contact_no', 'address')


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


class UserDetailsResponseSerializer(serializers.Serializer):
    user = UserProfileWithOrgAccessSerializer()

    class Meta:
        fields = ('user',)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class AdminUserResponseSerializer(serializers.Serializer):
    organization = OrganizationSerializer()
    users = UserProfileWithOrgAccessSerializer(many=True)

    class Meta:
        fields = ('organization', 'users',)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class RoleSerializer(serializers.ModelSerializer):
    orgID = serializers.UUIDField(source='organization.uuid')
    org = serializers.CharField(source='organization.name')
    role = serializers.CharField(source='user_role')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('orgID', 'org', 'role')

