# Generated by Django 2.0.6 on 2018-07-20 10:05

from django.db import migrations, models


def log(message):
    def fake_op(apps, schema_editor):
        print(message)
    return fake_op


def match_address_for_patient(apps, schema_editor):
    Patient = apps.get_model('phi', 'Patient')
    Add = apps.get_model('user_auth', 'Address')
    for patient in Patient.objects.all():
        try:
            add = Add.objects.get(id=patient.address)
            print(add.uuid)
            patient.temp_add = add.uuid
            patient.save()
        except Exception as e:
            print('Error: ', e)
            print('Address is empty for patient:', patient.first_name)


def match_patient_for_episode(apps, schema_editor):
    Episode = apps.get_model('phi', 'Episode')
    Patient = apps.get_model('phi', 'Patient')
    for episode in Episode.objects.all():
        try:
            patient = Patient.objects.get(id=episode.patient)
            print(patient.uuid)
            episode.temp_pat = patient.uuid
            episode.save()
        except Exception as e:
            print('Error:', e)
            print('Patient is empty for this episode')


def match_pharmacy_for_episode(apps, schema_editor):
    Episode = apps.get_model('phi', 'Episode')
    Organization = apps.get_model('user_auth', 'Organization')
    for episode in Episode.objects.all():
        try:
            pharmacy = Organization.objects.get(id=episode.pharmacy)
            print(pharmacy.uuid)
            episode.temp_phar = pharmacy.uuid
            episode.save()
        except Exception as e:
            print('Error:', e)
            print('Pharmacy is empty for this episode')


def match_primary_physician_for_episode(apps, schema_editor):
    Episode = apps.get_model('phi', 'Episode')
    Physician = apps.get_model('phi', 'Physician')
    for episode in Episode.objects.all():
        try:
            primary_physician = Physician.objects.get(id=episode.primary_physician)
            print(primary_physician.uuid)
            episode.temp_phy = primary_physician.uuid
            episode.save()
        except Exception as e:
            print('Error:', e)
            print('Primary Physician is empty for this episode')


def match_soc_clinician_for_episode(apps, schema_editor):
    Episode = apps.get_model('phi', 'Episode')
    SocClinician = apps.get_model('user_auth', 'UserProfile')
    for episode in Episode.objects.all():
        try:
            soc_clinician = SocClinician.objects.get(id=episode.soc_clinician)
            print(soc_clinician)
            episode.temp_soc_clinician = soc_clinician.uuid
            episode.save()
        except Exception as e:
            print('Error:', e)
            print('Soc Clinician is empty for this episode')


def match_attending_physician_for_episode(apps, schema_editor):
    Episode = apps.get_model('phi', 'Episode')
    AttendingPhysician = apps.get_model('user_auth', 'UserProfile')
    for episode in Episode.objects.all():
        try:
            attending_physician = AttendingPhysician.objects.get(id=episode.attending_physician)
            print(attending_physician)
            episode.temp_attending_physician = attending_physician.uuid
            episode.save()
        except Exception as e:
            print('Error:', e)
            print('Attending Physician is empty for this episode')


def match_episode_for_visit(apps, schema_editor):
    Visit = apps.get_model('phi', 'Visit')
    Episode = apps.get_model('phi', 'Episode')
    for visit in Visit.objects.all():
        try:
            episode = Episode.objects.get(id=visit.episode)
            print(episode)
            visit.temp_episode = episode.uuid
            visit.save()
        except Exception as e:
            print('Error:', e)
            print('Episode is empty for this visit')


def match_user_for_visit(apps, schema_editor):
    Visit = apps.get_model('phi', 'Visit')
    UserProfile = apps.get_model('user_auth', 'UserProfile')
    for visit in Visit.objects.all():
        try:
            user = UserProfile.objects.get(id=visit.user)
            print(user)
            visit.temp_user = user.uuid
            visit.save()
        except Exception as e:
            print('Error:', e)
            print('User is empty for this visit')


def match_fields_for_userepisodeaccess(apps, schema_editor):
    UserEpisodeAccess = apps.get_model('phi', 'UserEpisodeAccess')
    UserProfile = apps.get_model('user_auth', 'UserProfile')
    Org = apps.get_model('user_auth', 'Organization')
    Episode = apps.get_model('phi', 'Episode')
    for access in UserEpisodeAccess.objects.all():
        try:
            user = UserProfile.objects.get(id=access.user)
            print(user)
            access.temp_user = user.uuid
        except Exception as e:
            print('Error:', e)
            print('User is empty for this UserEpisodeAccess')
        try:
            episode = Episode.objects.get(id=access.episode)
            print(episode)
            access.temp_episode = episode.uuid
        except Exception as e:
            print('Error:', e)
            print('Episode is empty for this UserEpisodeAccess')
        try:
            org = Org.objects.get(id=access.organization)
            print(org)
            access.temp_org = org.uuid
        except Exception as e:
            print('Error:', e)
            print('Organization is empty for this UserEpisodeAccess')
        try:
            access.save()
        except Exception as e:
            print('Error:', e)
            print('Something went wrong while saving UserEpisodeAccess')


def match_fields_for_organizationpatientmapping(apps, schema_editor):
    OrgPatientsMapping = apps.get_model('phi', 'OrganizationPatientsMapping')
    Patient = apps.get_model('phi', 'Patient')
    Organization = apps.get_model('user_auth', 'Organization')
    for mapping in OrgPatientsMapping.objects.all():
        try:
            patient = Patient.objects.get(id=mapping.patient)
            print(patient)
            mapping.temp_pat = patient.uuid
        except Exception as e:
            print('Error:', e)
            print('Patient is empty for this OrganizationPatientsMapping')

        try:
            org = Organization.objects.get(id=mapping.organization)
            print(org)
            mapping.temp_org = org.uuid
        except Exception as e:
            print('Error:', e)
            print('Organization is empty for this OrganizationPatientsMapping')

        try:
            mapping.save()
        except Exception as e:
            print('Error during saving OrganizationPatientsMapping:', e)


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0017_auto_20180720_1002'),
        ('user_auth', '0008_auto_20180720_1002'),
    ]

    operations = [
        # Update Address in Patient
        migrations.RunPython(log('Update Address in Patient')),

        # Add temp field in Patient to store address_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='patient',
            name='temp_add',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_address_for_patient),

        # Remove address field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='patient', name='address'),

        # Rename temp field to address field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='patient', old_name='temp_add', new_name='address'),

        # Update Patient in Episode
        migrations.RunPython(log('Update Patient in Episode')),

        # Add temp field in Episode to store patient_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='episode',
            name='temp_pat',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_patient_for_episode),

        # Remove patient field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='episode', name='patient'),

        # Rename temp field to patient field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='episode', old_name='temp_pat', new_name='patient'),

        # Update Pharmacy in Episode
        migrations.RunPython(log('Update Pharmacy in Episode')),

        # Add temp field in Episode to store org_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='episode',
            name='temp_phar',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_pharmacy_for_episode),

        # Remove pharmacy field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='episode', name='pharmacy'),

        # Rename temp field to address field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='episode', old_name='temp_phar', new_name='pharmacy'),

        # Update Primary Physician in Episode
        migrations.RunPython(log('Update Primary Physician in Episode')),

        # Add temp field in Episode to store physician_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='episode',
            name='temp_phy',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_primary_physician_for_episode),

        # Remove primary_physician field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='episode', name='primary_physician'),

        # Rename temp field to primary_physician field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='episode', old_name='temp_phy', new_name='primary_physician'),

        # Update SOC Clinician in Episode
        migrations.RunPython(log('Update SOC Clinician in Episode')),

        # Add temp field in Episode to store user_profile_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='episode',
            name='temp_soc_clinician',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_soc_clinician_for_episode),

        # Remove primary_physician field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='episode', name='soc_clinician'),

        # Rename temp field to primary_physician field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='episode', old_name='temp_soc_clinician', new_name='soc_clinician'),

        # Update Attending Physician in Episode
        migrations.RunPython(log('Update Attending Physician in Episode')),

        # Add temp field in Episode to store user_profile_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='episode',
            name='temp_attending_physician',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_attending_physician_for_episode),

        # Remove attending_physician field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='episode', name='attending_physician'),

        # Rename temp field to attending_physician field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='episode', old_name='temp_attending_physician', new_name='attending_physician'),

        # Update Episode in Visit
        migrations.RunPython(log('Update Episode in Visit')),

        # Add temp field in Visit to store episode_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='visit',
            name='temp_episode',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_episode_for_visit),

        # Remove episode field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='visit', name='episode'),

        # Rename temp field to episode field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='visit', old_name='temp_episode', new_name='episode'),

        # Update User in Visit
        migrations.RunPython(log('Update User in Visit')),

        # Add temp field in Visit to store user_profile_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='visit',
            name='temp_user',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_user_for_visit),

        # Remove user field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='visit', name='user'),

        # Rename temp field to user field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='visit', old_name='temp_user', new_name='user'),

        # Update Episode, UserProfile and Org in UserEpisodeAccess
        migrations.RunPython(log('Update Episode, UserProfile, Org in UserEpisodeAccess')),

        # Add temp fields in UserEpisodeAccess to store episode_uuid, userprofile_uuid and org_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='temp_episode',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='temp_user',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='temp_org',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_fields_for_userepisodeaccess),

        # Remove user field
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='userepisodeaccess', name='user'),
        migrations.RemoveField(model_name='userepisodeaccess', name='organization'),
        migrations.RemoveField(model_name='userepisodeaccess', name='episode'),

        # Rename temp field to user field
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='userepisodeaccess', old_name='temp_user', new_name='user'),
        migrations.RenameField(
            model_name='userepisodeaccess', old_name='temp_episode', new_name='episode'),
        migrations.RenameField(
            model_name='userepisodeaccess', old_name='temp_org', new_name='organization'),

        # Update Patient and Org in OrganizationPatientMapping
        migrations.RunPython(log('Update Patient and Org in OrganizationPatientsMapping')),

        # Add temp fields in OrganizationPatientsMapping to store patient_uuid and org_uuid
        migrations.RunPython(log('Step 1')),
        migrations.AddField(
            model_name='organizationpatientsmapping',
            name='temp_pat',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='organizationpatientsmapping',
            name='temp_org',
            field=models.UUIDField(null=True),
        ),

        # Data migration
        migrations.RunPython(log('Step 2')),
        migrations.RunPython(match_fields_for_organizationpatientmapping),

        # Remove patient and org fields
        migrations.RunPython(log('Step 3')),
        migrations.RemoveField(model_name='organizationpatientsmapping', name='patient'),
        migrations.RemoveField(model_name='organizationpatientsmapping', name='organization'),

        # Rename temp field to patient and org fields
        migrations.RunPython(log('Step 4')),
        migrations.RenameField(
            model_name='organizationpatientsmapping', old_name='temp_pat', new_name='patient'),
        migrations.RenameField(
            model_name='organizationpatientsmapping', old_name='temp_org', new_name='organization'),
    ]
