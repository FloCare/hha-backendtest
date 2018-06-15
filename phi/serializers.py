from rest_framework import serializers
from phi import models
from user_auth import models as user_auth_models
from user_auth.serializers import AddressSerializer, OrganizationSerializer
from django.db import transaction


class PatientPlainObjectSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContact = serializers.CharField(source='emergency_contact')
    address_id = serializers.IntegerField()

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'primaryContact', 'emergencyContact', 'address_id',)


class PatientSerializerWeb(serializers.ModelSerializer):
    address = AddressSerializer()
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContact = serializers.CharField(source='emergency_contact')
    timestamp = serializers.DateTimeField(source='created_on')

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'primaryContact', 'emergencyContact', 'timestamp', 'address',)


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


class OrganizationPatientMappingSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField()
    patient_id = serializers.IntegerField()

    class Meta:
        model = models.OrganizationPatientsMapping
        fields = ('id', 'organization_id', 'patient_id')


class EpisodeSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField()

    class Meta:
        model = models.Episode
        fields = ('id', 'patient_id', 'soc_date', 'end_date', 'period', 'is_active',
                  'transportation_level', 'acuity_type', 'classification', 'allergies', 'pharmacy',
                  'soc_clinician', 'attending_physician', 'primary_physician')


class UserEpisodeAccessSerializer(serializers.ModelSerializer):
    episode_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    organization_id = serializers.IntegerField()

    class Meta:
        model = models.UserEpisodeAccess
        fields = ('episode_id', 'user_id', 'organization_id', 'user_role')
