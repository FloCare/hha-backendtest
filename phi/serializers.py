from rest_framework import serializers
from phi import models
from user_auth import models as user_auth_models
from user_auth.serializers import AddressSerializer
from django.db import transaction


class PatientSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.Patient
        fields = ('id', 'name', 'primary_contact', 'emergency_contact', 'created_on',
                  'archived', 'address',)

    def get_name(self, obj):
        if obj.first_name and obj.last_name:
            return '{} {}'.format(obj.first_name, obj.last_name)
        elif obj.first_name:
            return obj.first_name
        else:
            return obj.last_name

    def create(self, validated_data):
        try:
            with transaction.atomic():
                address = user_auth_models.Address.objects.create(**(validated_data.pop('address')))
                instance = models.Patient.objects.create(**validated_data, address=address)
                return instance
        except Exception as e:
            print('Error in writing:', e)
            return None

