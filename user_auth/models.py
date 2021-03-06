from django.db import models
from django.contrib.auth.models import User
from flocarebase.models import BaseModel
import uuid

# Generic Stuff


class Address(BaseModel):
    """
    Generic Address Format
    Can be a patient-address/organization-address etc.
    """
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment_no = models.CharField(max_length=10, null=True)
    street_address = models.CharField(max_length=255, null=True)
    zip = models.CharField(max_length=20, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=50, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)


# Create your models here.
class Organization(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)      # Todo: Make Enum
    address = models.ForeignKey(Address, null=True, on_delete=models.CASCADE, related_name='organizations')
    contact_no = models.CharField(max_length=15, null=True)

    def __str__(self):
        return self.name


# Home Health Agency specific fields - if any
# class HHAProfile(models.Model):
#     organization = models.OneToOneField(Organization, primary_key=True, on_delete=models.CASCADE)
#
#
# class PharmacyProfile(models.Model):
#     organization = models.OneToOneField(Organization, primary_key=True, on_delete=models.CASCADE)


# class HospitalProfile(models.Model):
#     organization = models.OneToOneField(Organization, primary_key=True, on_delete=models.CASCADE)
#     # Hospital specific fields


class UserProfile(BaseModel):
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=15, null=True)
    qualification = models.CharField(max_length=40, null=True)
    address = models.ForeignKey(Address, null=True, on_delete=models.CASCADE, related_name='user_profile')
    organizations = models.ManyToManyField(Organization, through='UserOrganizationAccess')

    def __str__(self):
        return str(self.id) + ' ' + self.user.username

    def soft_delete(self):
        [access.soft_delete() for access in self.org_accesses.all()]
        if self.visits and self.visits.exists():
            [visit.soft_delete() for visit in self.visits.all()]
        if self.reports and self.reports.exists():
            [report.soft_delete() for report in self.reports.all()]
        if self.episode_accesses and self.episode_accesses.exists():
            [access.soft_delete() for access in self.episode_accesses.all()]
        if self.org_accesses and self.org_accesses.exists():
            [access.soft_delete() for access in self.org_accesses.all()]
        super().soft_delete()


class UserOrganizationAccess(BaseModel):
    """
    Lists out the users of an organization
    """
    id = models.IntegerField(unique=True, auto_created=True, serialize=False, verbose_name='ID', null=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='user_accesses')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='org_accesses')
    user_role = models.CharField(max_length=100)   # Todo: Make enum
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.organization.name + '-' + str(self.user) + '-' + self.user_role

    class Meta:
        # A user can be an admin of 1 org only
        unique_together = ('user', 'is_admin',)

