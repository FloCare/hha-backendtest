from rest_framework import serializers
from phi import models
from user_auth import models as user_models
from user_auth.serializers import AddressSerializer


class PatientPlainObjectSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    primaryContact = serializers.CharField(source='primary_contact')
    dob = serializers.DateField(required=False)
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelationship = serializers.CharField(source='emergency_contact_relationship', required=False)
    address_id = serializers.UUIDField()

    class Meta:
        model = models.Patient
        fields = ('firstName', 'lastName', 'primaryContact', 'address_id', 'emergencyContactName',
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
    id = serializers.UUIDField(source='uuid')

    class Meta:
        model = models.Physician
        fields = ('id', 'npi', 'first_name', 'last_name', 'phone1', 'phone2', 'fax')


class PatientSerializerWeb(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
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
    userIds = serializers.ListField(child=serializers.UUIDField())

    class Meta:
        model = models.Patient
        fields = ('patient', 'userIds')


class PatientSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    address = AddressSerializer()
    name = serializers.SerializerMethodField()
    primaryContact = serializers.CharField(source='primary_contact')
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelation = serializers.CharField(source='emergency_contact_relationship', required=False)
    dob = serializers.DateField(required=False)
    timestamp = serializers.DateTimeField(source='created_on')

    class Meta:
        model = models.Patient
        fields = ('id', 'name', 'firstName', 'lastName', 'primaryContact', 'emergencyContactName', 'dob',
                  'emergencyContactNumber', 'emergencyContactRelation', 'timestamp', 'archived', 'address',)

    def get_name(self, obj):
        if obj.first_name and obj.last_name:
            return '{} {}'.format(obj.first_name, obj.last_name)
        elif obj.first_name:
            return obj.first_name
        else:
            return obj.last_name


class PatientListSerializer(serializers.ModelSerializer):
    patients = serializers.ListField(child=serializers.UUIDField())

    class Meta:
        model = models.Patient
        fields = ('patients',)


class PatientFailureSerializer(serializers.Serializer):
    error = serializers.CharField()
    id = serializers.UUIDField()

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
    organization_id = serializers.UUIDField()
    patient_id = serializers.UUIDField()

    class Meta:
        model = models.OrganizationPatientsMapping
        fields = ('id', 'organization_id', 'patient_id')


class EpisodeSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField()

    class Meta:
        model = models.Episode
        fields = ('patient_id', 'soc_date', 'end_date', 'period', 'is_active',
                  'transportation_level', 'acuity_type', 'classification', 'allergies', 'pharmacy',
                  'soc_clinician', 'attending_physician', 'primary_physician')


class UserEpisodeAccessSerializer(serializers.ModelSerializer):
    episode_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    organization_id = serializers.UUIDField()

    class Meta:
        model = models.UserEpisodeAccess
        fields = ('episode_id', 'user_id', 'organization_id', 'user_role')


# Todo: Allow for Address Update
class PatientUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    firstName = serializers.CharField(source='first_name', required=False)
    lastName = serializers.CharField(source='last_name', required=False)
    primaryContact = serializers.CharField(source='primary_contact', required=False)
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelationship = serializers.CharField(source='emergency_contact_relationship', required=False)
    dob = serializers.CharField(required=False)

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'primaryContact', 'emergencyContactName',
                  'emergencyContactNumber', 'emergencyContactRelationship', 'dob')


class VisitSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(required=False)
    visitID = serializers.CharField(source='client_visit_id', required=False)
    episodeId = serializers.IntegerField(source='episode_id', required=False)
    scheduledAt = serializers.DateTimeField(source='scheduled_at', required=False, format='YYYY-MM-DD')
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    class Meta:
        model = models.Visit
        fields = '__all__'
