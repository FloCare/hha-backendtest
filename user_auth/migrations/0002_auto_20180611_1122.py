# Generated by Django 2.0.6 on 2018-06-11 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hhaprofile',
            name='organization',
        ),
        migrations.RemoveField(
            model_name='pharmacyprofile',
            name='organization',
        ),
        migrations.AddField(
            model_name='address',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Address'),
        ),
        migrations.DeleteModel(
            name='HHAProfile',
        ),
        migrations.DeleteModel(
            name='PharmacyProfile',
        ),
    ]
