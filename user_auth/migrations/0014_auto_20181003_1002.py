# Generated by Django 2.0.6 on 2018-10-03 10:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0013_auto_20180817_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='deleted_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='deleted_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='userorganizationaccess',
            name='deleted_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deleted_at',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]
