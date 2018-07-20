from django.db import models
from django.utils import timezone
from user_auth import models as user_models
import uuid


class Diagnosis(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# Create your models here.
class Patient(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
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


# class Place(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     address = models.ForeignKey(user_models.Address, on_delete=models.CASCADE)


class Physician(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
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
class Episode(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
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
            episode += (' ' + self.soc_date)
        return episode


class Visit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_visit_id = models.CharField(max_length=50, null=True)

    episode = models.ForeignKey(Episode, related_name='visit', null=True, on_delete=models.CASCADE)
    # place = models.ForeignKey(Place, related_name='visit', null=True, on_delete=models.CASCADE)

    user = models.ForeignKey(user_models.UserProfile, related_name='visit', on_delete=models.CASCADE)

    # Todo: Should org be added?
    # organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE, null=True)

    scheduled_at = models.DateTimeField(null=True)
    is_done = models.BooleanField(default=False)
    # Todo: automatically updated when is_done is marked as True
    time_of_completion = models.DateTimeField(null=True)
    is_deleted = models.BooleanField(default=False)

    # Todo: Confirm fields for the extended visit context
    # visit_type = models.CharField()         # Todo: Or Enum ??
    # duration = models.TimeField()           # Or estimated time etc.

    def __str__(self):
        visit = self.episode.patient.first_name
        if self.episode.patient.last_name:
            visit += (' ' + self.episode.patient.last_name)
        visit += ('-' + self.user.user.username)
        if self.scheduled_at:
            visit += ('-' + str(self.scheduled_at))
        return visit

    def save(self, *args, **kwargs):
        self.time_of_completion = timezone.now()
        super().save(*args, **kwargs)


class UserEpisodeAccess(models.Model):
    """
    Used for faster querying - finding all episodes/patients for a particular user,
    through an organization
    """
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE)
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)            # Todo: Make Enum

    def __str__(self):
        return str(self.organization) + '--' + str(self.user) + '--' + str(self.episode)

    class Meta:
        unique_together = ('episode', 'organization', 'user',)


class OrganizationPatientsMapping(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.organization) + '--' + str(self.patient)

    class Meta:
        unique_together = ('organization', 'patient',)
