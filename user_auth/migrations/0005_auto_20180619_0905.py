# Generated by Django 2.0.6 on 2018-06-19 09:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0004_auto_20180618_1052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userorganizationaccess',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='org_role', to='user_auth.UserProfile'),
        ),
    ]
