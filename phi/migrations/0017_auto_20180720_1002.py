# Generated by Django 2.0.6 on 2018-07-20 10:02

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0016_auto_20180720_0957'),
        ('user_auth', '0007_auto_20180720_0957')
    ]

    operations = [
        migrations.AlterField(
            model_name='diagnosis',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='diagnosis',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='episode',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='organizationpatientsmapping',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='organizationpatientsmapping',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='patient',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='physician',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='physician',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='id',
            field=models.IntegerField(auto_created=True, serialize=False, unique=True, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='userepisodeaccess',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]