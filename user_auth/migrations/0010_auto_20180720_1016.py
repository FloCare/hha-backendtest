# Generated by Django 2.0.6 on 2018-07-20 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0009_update_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='organizations',
            field=models.ManyToManyField(through='user_auth.UserOrganizationAccess', to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Address'),
        ),
        migrations.AlterField(
            model_name='userorganizationaccess',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='userorganizationaccess',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='org_role', to='user_auth.UserProfile'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Address'),
        ),
    ]
