from rest_framework import serializers
from user_auth import models


class AddressSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    zipCode = serializers.CharField(source='zip', required=False)
    streetAddress = serializers.CharField(source='street_address', required=False)
    apartmentNo = serializers.CharField(source='apartment_no', required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    country = serializers.CharField(required=False)

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


class RoleSerializer(serializers.ModelSerializer):
    org = serializers.CharField(source='organization.name')
    role = serializers.CharField(source='user_role')

    class Meta:
        model = models.UserOrganizationAccess
        fields = ('org', 'role')
