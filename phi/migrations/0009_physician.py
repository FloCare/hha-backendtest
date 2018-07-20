# Generated by Django 2.0.6 on 2018-07-06 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0008_auto_20180702_1439'),
    ]

    operations = [
        migrations.CreateModel(
            name='Physician',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('npi', models.CharField(max_length=10)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('phone1', models.CharField(max_length=15, null=True)),
                ('phone2', models.CharField(max_length=15, null=True)),
                ('fax', models.CharField(max_length=15, null=True)),
            ],
        ),
    ]