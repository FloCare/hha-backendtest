# Generated by Django 2.0.6 on 2018-08-17 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0012_auto_20180816_1141'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='address',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userorganizationaccess',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userorganizationaccess',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
