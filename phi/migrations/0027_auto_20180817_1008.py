# Generated by Django 2.0.6 on 2018-08-17 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0026_auto_20180817_0645'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosis',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='episode',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='episode',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organizationpatientsmapping',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organizationpatientsmapping',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='physician',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='physician',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='userepisodeaccess',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='visit',
            name='created_by',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='visit',
            name='updated_by',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
