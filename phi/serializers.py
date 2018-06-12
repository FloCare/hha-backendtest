from rest_framework import serializers
from phi import models
from user_auth import models as user_auth_models
from user_auth.serializers import AddressSerializer
from django.db import transaction


class PatientSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    name = serializers.SerializerMethodField()
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContact = serializers.CharField(source='emergency_contact')
    timestamp = serializers.DateTimeField(source='created_on')

    class Meta:
        model = models.Patient
        fields = ('id', 'name', 'primaryContact', 'emergencyContact', 'timestamp',
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


class PatientListSerializer(serializers.ModelSerializer):
    patients = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = models.Patient
        fields = ('patients',)


class PatientFailureSerializer(serializers.Serializer):
    error = serializers.CharField()
    id = serializers.IntegerField()

    class Meta:
        fields = ('id', 'error',)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class PatientDetailsResponseSerializer(serializers.Serializer):
    success = PatientSerializer(many=True)
    failure = PatientFailureSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
