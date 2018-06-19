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


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = '__all__'


# class UserProfileSerializer(serializers.ModelSerializer):
#     first_name = serializers.CharField(source='user.first_name')
#     last_name = serializers.CharField(source='user.last_name')
#     username = serializers.CharField(source='user.username')
#     email = serializers.CharField(source='user.email')
#     is_admin = serializers.BooleanField(source='user.is_superuser', read_only=True)
#
#     class Meta:
#         model = models.UserProfile
#         fields = ('id', 'title', 'first_name', 'last_name', 'username', 'email', 'contact_no', 'qualification', 'address', 'is_admin')   # noqa


class UserProfileWithOrgAccessSerializer(serializers.ModelSerializer):
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
