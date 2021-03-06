from django.contrib import admin
from user_auth.models import Address, UserProfile, Organization, UserOrganizationAccess
from phi.models import Patient, Physician, Diagnosis, Episode, UserEpisodeAccess, OrganizationPatientsMapping, Visit

# Register your models here.
admin.site.register(Address)
admin.site.register(UserProfile)
admin.site.register(Organization)
admin.site.register(UserOrganizationAccess)
admin.site.register(Patient)
admin.site.register(Physician)
admin.site.register(Diagnosis)
admin.site.register(Episode)
admin.site.register(UserEpisodeAccess)
admin.site.register(OrganizationPatientsMapping)
admin.site.register(Visit)
