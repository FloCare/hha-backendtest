# Generated by Django 2.0.6 on 2018-06-20 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0006_auto_20180620_0943'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='hic_no',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='patient',
            name='medical_record_no',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
