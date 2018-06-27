from rest_framework import serializers
from user_auth import models


class AddressSerializer(serializers.ModelSerializer):
    zipCode = serializers.CharField(source='zip')
    streetAddress = serializers.CharField(source='street_address')

    class Meta:
        model = models.Address
        fields = ('id', 'apartment_no', 'streetAddress', 'zipCode', 'city', 'state', 'country', 'latitude', 'longitude',)

    def create(self, validated_data):
        """
        Create and return a new Address instance, given the validated data
        :param validated_data:
        :return:
        """
        return models.Address.objects.create(**validated_data)


# Todo: Make same as AddressSerializer, and delete this: Only difference apartment_no field.
# Todo: This serializer is created just to avoid change in web frontend the time being
class AddressSerializerForApp(serializers.ModelSerializer):
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
    class Meta:
        model = models.Organization
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    org = serializers.CharField(source='organization.name')
    role = serializers.CharField(source='user_role')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('org', 'role')


class UserProfileForAppSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    roles = RoleSerializer(many=True)

    class Meta:
        model = models.UserProfile
        fields = ('id', 'roles')


class UserProfileWithOrgAccessSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    first_name = serializers.CharField(source='user.user.first_name')
    last_name = serializers.CharField(source='user.user.last_name')
    username = serializers.CharField(source='user.user.username')
    email = serializers.CharField(source='user.user.email')
    title = serializers.CharField(source='user.title')
    contact_no = serializers.CharField(source='user.contact_no')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('id', 'title', 'first_name', 'last_name', 'username', 'contact_no', 'email', 'user_role')


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
