from django.db import models
from django.contrib.auth.models import User

# Generic Stuff


class Address(models.Model):
    """
    Generic Address Format
    Can be a patient-address/organization-address etc.
    """
    apartment_no = models.CharField(max_length=10, null=True)
    street_address = models.CharField(max_length=255, null=True)
    zip = models.CharField(max_length=20, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=50, null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)


# Create your models here.
class Organization(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)      # Todo: Make Enum
    address = models.ForeignKey(Address, null=True, on_delete=models.CASCADE)
    contact_no = models.CharField(max_length=15, null=True)


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


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    title = models.CharField(max_length=50)
    contact_no = models.CharField(max_length=15, null=True)
    qualification = models.CharField(max_length=40, null=True)
    address = models.ForeignKey(Address, null=True, on_delete=models.CASCADE)
    organizations = models.ManyToManyField(Organization, through='UserOrganizationAccess')


class UserOrganizationAccess(models.Model):
    """
    Lists out the users of an organization
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    user_role = models.CharField(max_length=100)   # Todo: Make enum
    is_admin = models.BooleanField(default=False)

    class Meta:
        # A user can be an admin of 1 org only
        unique_together = ('user', 'is_admin',)

