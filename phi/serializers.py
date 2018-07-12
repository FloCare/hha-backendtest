from rest_framework import serializers
from phi import models
from user_auth.serializers import AddressSerializer, AddressSerializerForApp


class PatientPlainObjectSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    primaryContact = serializers.CharField(source='primary_contact')
    dob = serializers.DateField(required=False)
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelationship = serializers.CharField(source='emergency_contact_relationship', required=False)
    address_id = serializers.IntegerField()

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'primaryContact', 'address_id', 'emergencyContactName',
        'emergencyContactNumber', 'emergencyContactRelationship', 'dob',)


class PhysicianObjectSerializer(serializers.ModelSerializer):
    npi = serializers.CharField()
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    phone1 = serializers.CharField()
    phone2 = serializers.CharField()
    fax = serializers.CharField()

    class Meta:
        model = models.Physician
        fields = ('npi', 'firstName', 'lastName', 'phone1', 'phone2', 'fax')


class PhysicianResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Physician
        fields = ('npi', 'first_name', 'last_name', 'phone1', 'phone2', 'fax')


class PatientSerializerWeb(serializers.ModelSerializer):
    address = AddressSerializer()
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    dob = serializers.DateField(required=False)
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelationship = serializers.CharField(source='emergency_contact_relationship', required=False)
    timestamp = serializers.DateTimeField(source='created_on')

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'dob', 'primaryContact', 'emergencyContactName',
        'emergencyContactNumber', 'emergencyContactRelationship', 'timestamp', 'address',)


class PatientWithUsersSerializer(serializers.ModelSerializer):
    patient = PatientSerializerWeb()
    userIds = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = models.Patient
        fields = ('patient', 'userIds')


class PatientSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    address = AddressSerializerForApp()
    name = serializers.SerializerMethodField()
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContact = serializers.CharField(source='emergency_contact')
    timestamp = serializers.DateTimeField(source='created_on')

    class Meta:
        model = models.Patient
        fields = ('id', 'name', 'firstName', 'lastName', 'primaryContact', 'emergencyContact', 'timestamp',
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
