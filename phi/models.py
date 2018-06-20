from django.db import models
from user_auth import models as user_models


class Diagnosis(models.Model):
    name = models.CharField(max_length=50)


# Create your models here.
class Patient(models.Model):
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
    emergency_contact = models.CharField(max_length=15, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)
    address = models.ForeignKey(user_models.Address, null=True, on_delete=models.CASCADE)
    medical_record_no = models.CharField(max_length=50, null=True)
    hic_no = models.CharField(max_length=50, null=True)

    organizations = models.ManyToManyField(user_models.Organization, through='OrganizationPatientsMapping')


# Todo: When to add episode
# Todo: Create Episode at the time of assigning patient to a user ???
class Episode(models.Model):
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
    primary_physician = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE, related_name='primary_episodes', null=True)          # noqa


class UserEpisodeAccess(models.Model):
    """
    Used for faster querying - finding all episodes/patients for a particular user,
    through an organization
    """
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.UserProfile, on_delete=models.CASCADE)
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)            # Todo: Make Enum


class OrganizationPatientsMapping(models.Model):
    organization = models.ForeignKey(user_models.Organization, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('organization', 'patient',)
