# Generated by Django 2.0.6 on 2018-08-29 17:26

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0013_auto_20180817_1008'),
        ('phi', '0028_visitmiles'),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(max_length=50, null=True)),
                ('updated_by', models.CharField(max_length=50, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_auth.UserProfile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportItem',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.CharField(max_length=50, null=True)),
                ('updated_by', models.CharField(max_length=50, null=True)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_items', to='phi.Report')),
                ('visit', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='report_item', to='phi.Visit')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
