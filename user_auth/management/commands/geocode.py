from django.core.management.base import BaseCommand, CommandError
import requests
from django.db import transaction
from user_auth.models import Address

url = 'https://maps.googleapis.com/maps/api/geocode/json'
key = 'AIzaSyDiWZ3198smjFepUa0ZAoHePSnSxuhTzRU'


class Command(BaseCommand):
    help = 'Add users to the DB from the CSV'

    def add_arguments(self, parser):
        # parser.add_argument('org', nargs='+', type=str)
        pass

    def update_address(self, address):
        addr = address.street_address
        zip = address.zip
        city = address.city
        state = address.state
        country = address.country

        if city:
            addr = addr + ', ' + city
        if state:
            addr = addr + ', ' + state
        if zip:
            addr = addr + ' ' + zip
        if country:
            addr = addr + ', ' + country

        print('Hitting address:', addr)
        params = {'address': addr, 'key': key}
        resp = requests.get(url, params=params, timeout=3)
        print('Response is: ', resp)

        # Parse resp and update lat long to db
        if 'results' in resp.json():
            results = resp.json()['results']
            if len(results) > 0 and 'geometry' in results[0]:
                geometry = results[0]['geometry']
                if 'location' in geometry:
                    location = geometry['location']
                    lat = location.get('lat')
                    long = location.get('lng')
                    with transaction.atomic():
                        address.latitude = lat
                        address.longitude = long
                        address.save()
                    print('Lat long Saved to db for addressId: %s' % (address.id))
                else:
                    print('Location not found in geometry')
            else:
                print('geometry not found in results')
        else:
            print('results not found in response')
        print('Done')


    def handle(self, *args, **options):
        addresses = Address.objects.filter(latitude=None).filter(longitude=None)
        self.stdout.write(self.style.SUCCESS('No. of addresses without lat-long: %s' % str(len(addresses))))
        for address in addresses:
            self.update_address(address)
        self.stdout.write(self.style.SUCCESS('Data insert completed.'))

