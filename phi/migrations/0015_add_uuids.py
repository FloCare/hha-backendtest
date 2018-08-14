# Generated by Django 2.0.6 on 2018-07-20 09:38

from django.db import migrations, models
import uuid


def create_diagnosis_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'Diagnosis')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


def create_episode_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'Episode')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


def create_orgpatientmapping_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'OrganizationPatientsMapping')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


def create_patient_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'Patient')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


def create_physician_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'Physician')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


def create_userepisodeaccess_uuid(apps, schema_editor):
    mappings = apps.get_model('phi', 'UserEpisodeAccess')
    for mapping in mappings.objects.all():
        mapping.uuid = uuid.uuid4()
        mapping.save()


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0014_visit'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosis',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_diagnosis_uuid),
        migrations.AlterField(
            model_name='diagnosis',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='episode',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_episode_uuid),
        migrations.AlterField(
            model_name='episode',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='organizationpatientsmapping',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_orgpatientmapping_uuid),
        migrations.AlterField(
            model_name='organizationpatientsmapping',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_patient_uuid),
        migrations.AlterField(
            model_name='patient',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='physician',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_physician_uuid),
        migrations.AlterField(
            model_name='physician',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='uuid',
            field=models.UUIDField(null=True, blank=True)
        ),
        migrations.RunPython(create_userepisodeaccess_uuid),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]