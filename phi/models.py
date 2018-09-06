from django.db import models
from flocarebase.models import BaseModel
from user_auth import models as user_models
import uuid
from django.db import transaction


class Diagnosis(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# Create your models here.
class Patient(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    title = models.CharField(max_length=10)
    dob = models.DateField(null=True)
    GENDER = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    )
    gender = models.CharField(
        max_length=2,
        choices=GENDER,
        default='M',
        null=True
    )
    primary_contact = models.CharField(max_length=15, null=True)
    emergency_contact_name = models.CharField(max_length=100, null=True)
    emergency_contact_number = models.CharField(max_length=15, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    address = models.ForeignKey(user_models.Address, null=True, on_delete=models.CASCADE)
    medical_record_no = models.CharField(max_length=50, null=True)
    hic_no = models.CharField(max_length=50, null=True)

    organizations = models.ManyToManyField(user_models.Organization, through='OrganizationPatientsMapping')

    def __str__(self):
        patient_identifier = self.first_name
        if self.last_name:
            patient_identifier += (' ' + self.last_name)
        if self.dob:
            patient_identifier += (' ' + str(self.dob))
        return patient_identifier


# class Place(BaseModel):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     address = models.ForeignKey(user_models.Address, on_delete=models.CASCADE)


class Physician(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    npi = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone1 = models.CharField(max_length=15, null=True)
    phone2 = models.CharField(max_length=15, null=True)
    fax = models.CharField(max_length=15, null=True)

    def __str__(self):
        physician = self.first_name
        if self.last_name:
            physician += (' ' + self.last_name)
        if self.npi:
            physician += ('--' + self.npi)
        return physician


# Todo: When to add episode
# Todo: Create Episode at the time of assigning patient to a user ???
class Episode(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='episodes')
    soc_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    period = models.IntegerField(null=True)                     # In Days
    is_active = models.BooleanField(default=True)

    diagnosis = models.ManyToManyField(Diagnosis)
    CPR = (
        ('DNR', 'DNR'),
        ('FULL', 'FULL_CODE'),
        ('LTD', 'LIMITED_CODE'),
    )
    cpr_code = models.CharField(
        max_length=4,
        choices=CPR,
        default='DNR',
        null=True
    )
    TRANSPORTATION_LEVEL = (
        ('1', 'TAL-1'),
        ('2', 'TAL-2'),
        ('3', 'TAL-3'),
    )
    transportation_level = models.CharField(
        max_length=2,
        choices=TRANSPORTATION_LEVEL,
        default='1',
        null=True
    )
    ACUITY = (
        ('R', 'RED'),
        ('Y', 'YELLOW'),
        ('O', 'ORANGE'),
        ('G', 'GREEN'),
    )
    acuity_type = models.CharField(
        max_length=2,
        choices=ACUITY,
        default='R',
        null=True
    )
    classification = models.CharField(max_length=100, null=True)
    allergies = models.CharField(max_length=100, null=True)

    pharmacy = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE, null=True)

    soc_clinician = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE, related_name='soc_episodes', null=True)
    attending_physician = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE, related_name='attending_episodes', null=True)      # noqa
    primary_physician = models.ForeignKey(Physician, on_delete=models.CASCADE, related_name='primary_episodes', null=True)          # noqa

    def __str__(self):
        episode = str(self.patient)
        if self.soc_date:
            episode += (' ' + str(self.soc_date))
        return episode


class Visit(BaseModel):
    id = models.UUIDField(primary_key=True, editable=False)

    episode = models.ForeignKey(Episode, related_name='visit', null=True, on_delete=models.CASCADE)
    # place = models.ForeignKey(Place, related_name='visit', null=True, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.UserProfile, related_name='visit', on_delete=models.CASCADE)
    # Organization is added to Visit to make Querying Visits from same Org easier.
    # This is reduntant info, otherwise can be obtained using UserEpisodeAccess Model
    organization = models.ForeignKey(user_models.Organization, related_name='visits', on_delete=models.CASCADE, null=True)

    midnight_epoch = models.CharField(max_length=20, null=True)
    planned_start_time = models.DateTimeField(null=True)

    is_done = models.BooleanField(default=False)
    time_of_completion = models.DateTimeField(null=True)
    is_deleted = models.NullBooleanField(default=False, null=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            try:
                self.report_item.save()
                self.report_item.report.save()
            except ReportItem.DoesNotExist:
                pass

    def __str__(self):
        visit = self.episode.patient.first_name
        if self.episode.patient.last_name:
            visit += (' ' + self.episode.patient.last_name)
        visit += ('-' + self.user.user.username)
        if self.midnight_epoch:
            visit += ('-' + str(self.midnight_epoch))
        if self.planned_start_time:
            visit += ('-' + str(self.planned_start_time))
        return visit


class VisitMiles(BaseModel):
    uuid = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.OneToOneField(Visit, related_name='visit_miles', on_delete=models.CASCADE)
    odometer_start = models.FloatField(null=True)
    odometer_end = models.FloatField(null=True)
    total_miles = models.FloatField(null=True)
    # TODO Enforce check on app side? -- VARCHAR like equivalent ?? Take space only if required
    miles_comments = models.CharField(null=True, max_length=300)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            super().save(*args, **kwargs)
            try:
                self.visit.save()
            except Visit.DoesNotExist:
                pass

    def __str__(self):
        return str(self.visit) + '--' + str(self.odometer_start) + ' -- ' + str(self.odometer_end) + ' -- ' +\
               str(self.total_miles)


class UserEpisodeAccess(BaseModel):
    """
    Used for faster querying - finding all episodes/patients for a particular user,
    through an organization
    """
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE)
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)            # Todo: Make Enum

    def __str__(self):
        return str(self.organization) + '--' + str(self.user) + '--' + str(self.episode)

    class Meta:
        unique_together = ('episode', 'organization', 'user',)


class OrganizationPatientsMapping(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.organization) + '--' + str(self.patient)

    class Meta:
        unique_together = ('organization', 'patient',)


class Report(BaseModel):
    uuid = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.uuid) + str(self.user)


class ReportItem(BaseModel):
    uuid = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, related_name='report_items', on_delete=models.CASCADE)
    visit = models.OneToOneField(Visit, related_name='report_item', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.report) + str(self.visit)