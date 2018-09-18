from rest_framework import serializers
from user_auth.serializers import AddressSerializer
from user_auth.serializers import AddressIDWithLatLngSerializer
from user_auth.response_serializers import UserProfileResponseSerializer
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


class PatientWithAddressSerializer(serializers.ModelSerializer):
    patientID = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    address = AddressIDWithLatLngSerializer()
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.Patient
        fields = ('patientID', 'name', 'firstName', 'lastName', 'address')

    def get_name(self, obj):
        if obj.first_name and obj.last_name:
            return '{} {}'.format(obj.first_name, obj.last_name)
        elif obj.first_name:
            return obj.first_name
        else:
            return obj.last_name


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


class PhysicianResponseSerializer(serializers.ModelSerializer):
    physicianID = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')

    class Meta:
        model = models.Physician
        fields = ('physicianID', 'npi', 'firstName', 'lastName', 'phone1', 'phone2', 'fax')


class EpisodeWithPatientsResponseSerializer(serializers.ModelSerializer):
    episodeID = serializers.UUIDField(source='uuid', required=False)
    patient = PatientWithAddressSerializer()

    class Meta:
        model = models.Episode
        fields = ('episodeID', 'patient')


class EpisodeResponseSerializer(serializers.ModelSerializer):
    episodeID = serializers.UUIDField(source='uuid', required=False)
    patientID = serializers.UUIDField(source='patient_id', required=False)
    socDate = serializers.DateField(source='soc_date', required=False)
    endDate = serializers.DateField(source='end_date', required=False)
    transportationLevel = serializers.CharField(source='transportation_level', required=False)
    acuityType = serializers.CharField(source='acuity_type', required=False)
    socClinician = UserProfileResponseSerializer(source='soc_clinician', required=False)
    attendingPhysician = UserProfileResponseSerializer(source='attending_physician', required=False)
    primaryPhysician = PhysicianResponseSerializer(source='primary_physician', required=False)

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


class VisitForOrgResponseSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source='id')
    userID = serializers.UUIDField(source='user_id')
    episode = EpisodeWithPatientsResponseSerializer()
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)
    plannedStartTime = serializers.SerializerMethodField(required=False)

    def get_plannedStartTime(self, obj):
        t = obj.planned_start_time
        if t:
            return t.isoformat()
        return None

    class Meta:
        model = models.Visit
        fields = ('visitID', 'userID', 'episode', 'timeOfCompletion', 'isDone', 'isDeleted', 'plannedStartTime')


class VisitMilesResponseSerializer(serializers.ModelSerializer):
    odometerStart = serializers.FloatField(source='odometer_start', allow_null=True)
    odometerEnd = serializers.FloatField(source='odometer_end', allow_null=True)
    totalMiles = serializers.FloatField(source='total_miles', allow_null=True)
    milesComments = serializers.CharField(source='miles_comments', allow_null=True)

    class Meta:
        model = models.VisitMiles
        fields = ('odometerStart', 'odometerEnd', 'totalMiles', 'milesComments')


class VisitResponseSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source='id')
    userID = serializers.UUIDField(source='user_id')
    episodeID = serializers.UUIDField(source="episode_id", required=False)
    placeID = serializers.UUIDField(source='place_id', required=False)
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)
    midnightEpochOfVisit = serializers.SerializerMethodField(required=False)
    plannedStartTime = serializers.SerializerMethodField(required=False)
    visitMiles = VisitMilesResponseSerializer(source='visit_miles')
    reportID = serializers.SerializerMethodField(required=False)

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    def get_reportID(self, obj):
        try:
            return obj.report_item.report.uuid
        except Exception:
            return None

    def get_midnightEpochOfVisit(self, obj):
        t = obj.midnight_epoch
        if t:
            try:
                return int(t)
            except Exception as e:
                print('Error in fetching timestamp:', str(e))
        return None

    def get_plannedStartTime(self, obj):
        t = obj.planned_start_time
        if t:
            return t.isoformat()
        return None

    class Meta:
        model = models.Visit
        fields = ('visitID', 'userID', 'episodeID', 'placeID', 'timeOfCompletion', 'isDone', 'isDeleted',
                  'midnightEpochOfVisit', 'plannedStartTime', 'visitMiles', 'reportID')


class VisitResponseForReportSerializer(serializers.ModelSerializer):
    visitID = serializers.UUIDField(source='id')
    # userID = serializers.UUIDField(source='user_id')
    user = serializers.SerializerMethodField(required=False)
    name = serializers.SerializerMethodField(required=False)
    # episodeID = serializers.UUIDField(source="episode_id", required=False)
    timeOfCompletion = serializers.DateTimeField(source='time_of_completion', required=False)
    isDone = serializers.BooleanField(source='is_done', required=False)
    isDeleted = serializers.BooleanField(source='is_deleted', required=False)
    # midnightEpochOfVisit = serializers.SerializerMethodField(required=False)
    # plannedStartTime = serializers.SerializerMethodField(required=False)
    visitMiles = VisitMilesResponseSerializer(source='visit_miles')
    address = serializers.SerializerMethodField(required=False)

    def create(self, validated_data):
        return self.Meta.model.objects.create(**validated_data)

    def get_user(self, obj):
        name = obj.user.user.last_name + ' ' + obj.user.user.first_name
        return name

    def get_name(self, obj):
        if obj.episode:
            return obj.episode.patient.first_name + ' ' + obj.episode.patient.last_name
        else:
            return obj.place.name

    def get_address(self, obj):
        if obj.episode:
            address_object = obj.episode.patient.address
        elif obj.place:
            address_object = obj.place.address
        else:
            return " "
        return self.get_formatted_address(address_object)

    def get_formatted_address(self, address):
        return address.street_address + ', ' + address.city + ', ' + address.state + ', ' + address.country + ', ' + address.zip

    class Meta:
        model = models.Visit
        fields = ('visitID', 'user', 'name', 'address', 'timeOfCompletion', 'isDone', 'isDeleted', 'visitMiles')


class VisitDetailsResponseSerializer(serializers.Serializer):
    success = VisitResponseSerializer(many=True)
    failure = FailureResponseSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


# Todo: Temporary Serializer to support migrating apps from 0.2.0 to Next Version
class PatientWithOldIdsSerializer(serializers.ModelSerializer):
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
        fields = ('id', 'patientID', 'name', 'firstName', 'lastName', 'primaryContact', 'emergencyContactName', 'dob',
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


# Todo: Temporary Serializer to support migrating apps from 0.2.0 to Next Version
class PatientDetailsWithOldIdsResponseSerializer(serializers.Serializer):
    success = PatientWithOldIdsSerializer(many=True)
    failure = FailureResponseSerializer(many=True)

    class Meta:
        fields = ('success', 'failure')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ReportSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="uuid")
    user = UserProfileResponseSerializer()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    itemCount = serializers.SerializerMethodField()

    class Meta:
        model = models.Report
        fields = ('id', 'user', 'created_at', 'updated_at', 'itemCount')

    def get_itemCount(self, obj):
        if obj.report_items:
            return obj.report_items.count()
        return 0


class ReportItemSerializer(serializers.ModelSerializer):
    reportItemId = serializers.UUIDField(source="uuid")
    visitID = serializers.SerializerMethodField()

    def get_visitID(self, obj):
        return obj.visit.id

    class Meta:
        model = models.ReportItem
        fields = ('reportItemId', 'visitID')


class ReportDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="report.uuid")
    reportItems = ReportItemSerializer(source='report_items', many=True)

    class Meta:
        fields = ('id', 'reportItems')

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


# Todo: Duplicate. Remove in favor of ReportDetailSerializer
class ReportDetailsForWebSerializer(serializers.ModelSerializer):
    reportID = serializers.UUIDField(source='report.uuid')
    reportCreatedAt = serializers.DateTimeField(source='report.created_at')
    visit = VisitResponseForReportSerializer()

    class Meta:
        model = models.ReportItem
        fields = ('reportID', 'reportCreatedAt', 'visit',)


class PlaceResponseSerializer(serializers.ModelSerializer):
    placeID = serializers.UUIDField(source='uuid')
    contactNumber = serializers.CharField(source='contact_number', required=False)
    name = serializers.CharField()
    address = AddressSerializer()

    class Meta:
        model = models.Place
        fields = ('placeID', 'contactNumber', 'name', 'address')



# Todo: Used for online patients feature in the app
class PatientsForOrgSerializer(serializers.ModelSerializer):
    patientID = serializers.UUIDField(source='patient.uuid')
    firstName = serializers.CharField(source='patient.first_name')
    lastName = serializers.CharField(source='patient.last_name')
    address = AddressSerializer(source='patient.address')

    class Meta:
        model = models.OrganizationPatientsMapping
        fields = ('patientID', 'firstName', 'lastName', 'address',)
