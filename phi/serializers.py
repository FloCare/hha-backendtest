from rest_framework import serializers
from phi import models
from user_auth.serializers import AddressSerializer
import datetime
import dateutil
import logging

logger = logging.getLogger(__name__)


class PatientPlainObjectSerializer(serializers.ModelSerializer):
    patientID = serializers.UUIDField(source='uuid', required=False)
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
        fields = ('patientID', 'firstName', 'lastName', 'primaryContact', 'address_id', 'emergencyContactName',
                  'emergencyContactNumber', 'emergencyContactRelationship', 'dob',)


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


class PatientWithUsersAndPhysiciansSerializer(serializers.ModelSerializer):
    patient = PatientSerializerWeb()
    userIds = serializers.ListField(child=serializers.UUIDField())
    physicianId = serializers.UUIDField()

    class Meta:
        model = models.Patient
        fields = ('patient', 'userIds', 'physicianId')


class OrganizationPatientMappingSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField()
    patient_id = serializers.UUIDField()

    class Meta:
        model = models.OrganizationPatientsMapping
        fields = ('id', 'organization_id', 'patient_id')


class EpisodeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    socDate = serializers.DateField(source='soc_date', required=False, allow_null=True)
    endDate = serializers.DateField(source='end_date', required=False, allow_null=True)
    transportationLevel = serializers.CharField(source='transportation_level', required=False, allow_null=True)
    acuityType = serializers.CharField(source='acuity_type', required=False, allow_null=True)
    socClinician = serializers.UUIDField(source='soc_clinician_id', required=False, allow_null=True)
    attendingPhysician = serializers.UUIDField(source='attending_physician_id', required=False, allow_null=True)
    primaryPhysician = serializers.UUIDField(source='primary_physician_id', required=False, allow_null=True)

    class Meta:
        model = models.Episode
        fields = ('id', 'patient', 'socDate', 'endDate', 'period', 'allergies',
                  'transportationLevel', 'acuityType', 'classification', 'pharmacy',
                  'socClinician', 'attendingPhysician', 'primaryPhysician')


class UserEpisodeAccessSerializer(serializers.ModelSerializer):
    episode_id = serializers.UUIDField()
    user_id = serializers.UUIDField()
    organization_id = serializers.UUIDField()

    class Meta:
        model = models.UserEpisodeAccess
        fields = ('episode_id', 'user_id', 'organization_id', 'user_role')


class PatientUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', required=False)
    firstName = serializers.CharField(source='first_name', required=False)
    lastName = serializers.CharField(source='last_name', required=False)
    primaryContact = serializers.CharField(source='primary_contact', required=False)
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False)
    emergencyContactNumber = serializers.CharField(source='emergency_contact_number', required=False)
    emergencyContactRelationship = serializers.CharField(source='emergency_contact_relationship', required=False)
    dob = serializers.CharField(required=False)
    address = AddressSerializer(required=False)

    class Meta:
        model = models.Patient
        fields = ('id', 'firstName', 'lastName', 'primaryContact', 'emergencyContactName',
                  'emergencyContactNumber', 'emergencyContactRelationship', 'dob', 'address')

    def update(self, instance, validated_data):
        print('validated data is:', validated_data)
        if 'address' in validated_data:
            address = validated_data.get('address')
            # Todo: Hacky!
            if ('street_address' in address) and ('zip' in address) and ('city' in address) and \
                ('state' in address) and ('country' in address):
                instance.address.street_address = address.get('street_address', None)
                instance.address.zip = address.get('zip', None)
                instance.address.city = address.get('city', None)
                instance.address.state = address.get('state', None)
                instance.address.country = address.get('country', None)
                instance.address.latitude = address.get('latitude', None)
                instance.address.longitude = address.get('longitude', None)
            if 'apartment_no' in address:
                instance.address.apartment_no = address.get('apartment_no', None)
            instance.address.save()
        else:
            instance.address = instance.address
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.primary_contact = validated_data.get('primary_contact', instance.primary_contact)
        instance.emergency_contact_name = validated_data.get('emergency_contact_name', instance.emergency_contact_name)
        instance.emergency_contact_number = validated_data.get('emergency_contact_number', instance.emergency_contact_number)
        instance.emergency_contact_relationship = validated_data.get('emergency_contact_relationship', instance.emergency_contact_relationship)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.save()
        return instance


class VisitSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source='id')
    userID = serializers.UUIDField(source="user_id", required=False)
    episodeID = serializers.UUIDField(source="episode_id", required=False, allow_null=True)
    placeID = serializers.UUIDField(source="place_id", required=False, allow_null=True)
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)
    midnightEpochOfVisit = serializers.CharField(source='midnight_epoch', required=False)
    plannedStartTime = serializers.CharField(source='planned_start_time', required=False)
    organizationID = serializers.UUIDField(source='organization_id', required=False)

    def validate_midnightEpochOfVisit(self, obj):
        try:
            if obj:
                ms = int(obj)
                datetime.datetime.fromtimestamp(ms/1000.0)
                return obj
        except Exception as e:
            logger.error('Error in parsing midnightEpochOfVisit: %s' % str(e))
            raise serializers.ValidationError('midnightEpochOfVisit format is not correct')
        return None

    def validate_plannedStartTime(self, obj):
        if obj:
            try:
                ts = dateutil.parser.parse(obj)
                return ts
            except Exception as e:
                logger.error('Parse error in plannedStartTime: %s' % str(e))
                raise serializers.ValidationError('plannedStartTime format is not ISO 8601')
        return None

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    class Meta:
        model = models.Visit
        fields = ('visitID', 'userID', 'episodeID', 'timeOfCompletion', 'isDone', 'isDeleted', 'placeID',
                  'midnightEpochOfVisit', 'plannedStartTime', 'organizationID')


class VisitMilesSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source="visit_id", required=False)
    odometerStart = serializers.FloatField(source='odometer_start', required=False, allow_null=True)
    odometerEnd = serializers.FloatField(source='odometer_end', required=False, allow_null=True)
    totalMiles = serializers.FloatField(source='computed_miles', required=False, allow_null=True)
    milesComments = serializers.CharField(source='miles_comments', required=False, allow_null=True)

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    class Meta:
        model = models.VisitMiles
        fields = ('odometerStart', 'odometerEnd', 'totalMiles', 'milesComments', 'visitID')


class PlaceUpdateSerializer(serializers.ModelSerializer):
    contactNumber = serializers.CharField(source='contact_number', required=False, allow_null=True)
    name = serializers.CharField()

    class Meta:
        model = models.Place
        fields = ('contactNumber', 'name')

