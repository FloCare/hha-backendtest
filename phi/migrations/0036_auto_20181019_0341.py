# Generated by Django 2.0.6 on 2018-10-19 03:41
from phi.constants import MILES_COMMENTS_DEFAULT_TEXT

from django.db import migrations


def update_comments_and_total_miles(apps, schema_editor):
    VisitMiles = apps.get_model('phi', 'VisitMiles')

    for VisitMile in VisitMiles.objects.all():
        try:
            odometer_start = VisitMile.odometer_start
            odometer_end = VisitMile.odometer_end
            miles_comments = ''
            if odometer_start:
                miles_comments += 'OdometerStart: %s; ' % str(odometer_start)
            if odometer_end:
                miles_comments += 'OdometerEnd: %s; ' % str(odometer_end)

            initial_comment = VisitMile.miles_comments
            if initial_comment and initial_comment.strip():
                miles_comments += ('%s' % str(initial_comment))

            print('')
            if (odometer_start and odometer_end) and (not VisitMile.total_miles):
                total_miles = odometer_end-odometer_start
                print('Updating total_miles to: ', total_miles)
                VisitMile.total_miles = total_miles
            else:
                print('Not updating total_miles')

            print('New Miles Comments:', miles_comments)
            print('')
            VisitMile.miles_comments = miles_comments
            VisitMile.save()
        except Exception as e:
            print('Skipping record: %s, Error: %s' % (str(VisitMile.uuid), str(e)))


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0035_auto_20181008_1110'),
    ]

    operations = [
        migrations.RunPython(update_comments_and_total_miles),
    ]
