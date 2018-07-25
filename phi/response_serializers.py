from rest_framework import serializers
from user_auth.serializers import AddressSerializer
from user_auth.response_serializers import UserProfileResponseSerializer
from phi.serializers import PhysicianObjectSerializer
from phi import models


class PatientListSerializer(serializers.ModelSerializer):
    patients = serializers.ListField(child=serializers.UUIDField())

    class Meta:
        model = models.Patient
        fields = ('patients',)


class PatientSerializer(serializers.ModelSerializer):
    patientID = serializers.UUIDField(source='uuid')
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
    episodeID = serializers.SerializerMethodField()

    class Meta:
        model = models.Patient
        fields = ('patientID', 'name', 'firstName', 'lastName', 'primaryContact', 'emergencyContactName', 'dob',
                  'emergencyContactNumber', 'emergencyContactRelation', 'timestamp', 'archived', 'address', 'episodeID')

    def get_name(self, obj):
        if obj.first_name and obj.last_name:
            return '{} {}'.format(obj.first_name, obj.last_name)
        elif obj.first_name:
            return obj.first_name
        else:
            return obj.last_name

    def get_episodeID(self, obj):
        return obj.episodes.get(is_active=True).uuid


class FailureResponseSerializer(serializers.Serializer):
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
    failure = FailureResponseSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class EpisodeResponseSerializer(serializers.ModelSerializer):
    episodeID = serializers.UUIDField(source='uuid', required=False)
    patientID = serializers.UUIDField(source='patient_id', required=False)
    socDate = serializers.DateField(source='soc_date', required=False)
    endDate = serializers.DateField(source='end_date', required=False)
    transportationLevel = serializers.CharField(source='transportation_level', required=False)
    acuityType = serializers.CharField(source='acuity_type', required=False)
    socClinician = UserProfileResponseSerializer(source='soc_clinician', required=False)
    attendingPhysician = UserProfileResponseSerializer(source='attending_physician', required=False)
    primaryPhysician = PhysicianObjectSerializer(source='primary_physician', required=False)

    class Meta:
        model = models.Episode
        fields = ('episodeID', 'patientID', 'socDate', 'endDate', 'period', 'allergies',
                  'transportationLevel', 'acuityType', 'classification', 'pharmacy',
                  'socClinician', 'attendingPhysician', 'primaryPhysician')


class EpisodeDetailsResponseSerializer(serializers.Serializer):
    success = EpisodeResponseSerializer(many=True)
    failure = FailureResponseSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class VisitResponseSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source='id')
    userID = serializers.UUIDField(source='user_id')
    episodeID = serializers.UUIDField(source="episode_id", required=False)
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)
    midnightEpochOfVisit = serializers.IntegerField(source='midnight_epoch', required=False)
    # Todo: This field needs to be improved
    plannedStartTime = serializers.TimeField(source='planned_start_time', required=False)

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    class Meta:
        model = models.Visit
        fields = ('visitID', 'userID', 'episodeID', 'timeOfCompletion', 'isDone', 'isDeleted',
                  'midnightEpochOfVisit', 'plannedStartTime')


class VisitDetailsResponseSerializer(serializers.Serializer):
    success = VisitResponseSerializer(many=True)
    failure = FailureResponseSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
