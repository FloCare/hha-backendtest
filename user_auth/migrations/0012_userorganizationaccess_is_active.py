# Generated by Django 2.0.6 on 2018-08-06 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0011_auto_20180723_1127'),
    ]

    operations = [
        migrations.AddField(
            model_name='userorganizationaccess',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
