from rest_framework import serializers
from user_auth.serializers.serializers import AddressSerializer
from phi.models import *


class CreatePlaceRequestSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=100)
    contactNumber = serializers.CharField(source='contact_number', max_length=20, required=False, default=None,
                                          allow_null=True)
    address = AddressSerializer()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class CreatePhysicianRequestSerializer(serializers.Serializer):
    npi = serializers.CharField(max_length=20)
    firstName = serializers.CharField(source='first_name', max_length=100)
    lastName = serializers.CharField(source='last_name', max_length=100)
    phone1 = serializers.CharField(required=False)
    phone2 = serializers.CharField(required=False, allow_null=True)
    fax = serializers.CharField(required=False)

    def create(self, validated_data, **kwargs):
        return Physician.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.phone2 = validated_data.get('phone2', instance.phone2)
        instance.save()
        return instance
