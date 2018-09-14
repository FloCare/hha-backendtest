from rest_framework import serializers
from user_auth.serializers import AddressSerializer


class CreatePlaceRequestSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=100)
    contactNumber = serializers.CharField(source='contact_number', max_length=20, required=False, default=None)
    address = AddressSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass