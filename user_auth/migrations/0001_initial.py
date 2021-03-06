# Generated by Django 2.0.6 on 2018-06-11 01:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('apartment_no', models.CharField(max_length=10, null=True)),
                ('street_address', models.CharField(max_length=255, null=True)),
                ('zip', models.IntegerField(null=True)),
                ('city', models.CharField(max_length=100, null=True)),
                ('state', models.CharField(max_length=50, null=True)),
                ('country', models.CharField(max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=50)),
                ('contact_no', models.CharField(max_length=15, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserOrganizationAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_role', models.CharField(max_length=100)),
                ('is_admin', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('contact_no', models.CharField(max_length=15, null=True)),
                ('qualification', models.CharField(max_length=40, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='HHAProfile',
            fields=[
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='user_auth.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='PharmacyProfile',
            fields=[
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='user_auth.Organization')),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='organizations',
            field=models.ManyToManyField(through='user_auth.UserOrganizationAccess', to='user_auth.Organization'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userorganizationaccess',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.Organization'),
        ),
        migrations.AddField(
            model_name='userorganizationaccess',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserProfile'),
        ),
        migrations.AddField(
            model_name='organization',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_auth.Address'),
        ),
    ]
