from django.db import migrations


def add_visit_miles_for_existing_visits(apps, _):
    visit_model = apps.get_model('phi', 'Visit')
    visit_miles_model = apps.get_model('phi', 'VisitMiles')
    for visit in visit_model.objects.all():
        try:
            if visit.visit_miles:
                print('has visit miles, skipping for :', str(visit.id), str(visit.created_at))
                pass
        except visit_miles_model.DoesNotExist:
            print('adding visit miles for visitID:', str(visit.id), str(visit.created_at))
            visit_miles = visit_miles_model(visit=visit)
            visit_miles.save()


class Migration(migrations.Migration):

    dependencies = [
        ('phi', '0028_report_reportitem_visitmiles'),
    ]

    operations = [
        migrations.RunPython(add_visit_miles_for_existing_visits),
    ]
