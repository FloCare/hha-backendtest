# Generated by Django 2.0.6 on 2018-07-20 10:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0010_auto_20180720_1016'),
        ('phi', '0018_update_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='episode',
            name='diagnosis',
            field=models.ManyToManyField(to='phi.Diagnosis'),
        ),
        migrations.AddField(
            model_name='patient',
            name='organizations',
            field=models.ManyToManyField(through='phi.OrganizationPatientsMapping', to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='attending_physician',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attending_episodes', to='user_auth.UserProfile'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='phi.Patient'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='pharmacy',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='primary_physician',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='primary_episodes', to='phi.Physician'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='soc_clinician',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='soc_episodes', to='user_auth.UserProfile'),
        ),
        migrations.AlterField(
            model_name='organizationpatientsmapping',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='organizationpatientsmapping',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='phi.Patient'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Address'),
        ),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='episode',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='phi.Episode'),
        ),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.Organization'),
        ),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserProfile'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='episode',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='visit', to='phi.Episode'),
        ),
        migrations.AlterField(
            model_name='visit',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='visit', to='user_auth.UserProfile'),
        ),
    ]
