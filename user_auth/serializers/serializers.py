from rest_framework import serializers
from user_auth import models


# Used in PHI module. Remove when refactoring them
class AddressSerializer(serializers.ModelSerializer):
    addressID = serializers.UUIDField(source='uuid', required=False)
    zipCode = serializers.CharField(source='zip', required=False)
    streetAddress = serializers.CharField(source='street_address', required=False)
    apartmentNo = serializers.CharField(source='apartment_no', required=False, allow_null=True)
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


class AddressIDWithLatLngSerializer(serializers.ModelSerializer):
    addressID = serializers.UUIDField(source='uuid', required=False)

    class Meta:
        model = models.Address
        fields = ('addressID', 'latitude', 'longitude',)
