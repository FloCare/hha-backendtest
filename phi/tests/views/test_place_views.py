from flocarebase.common.test_helpers import UserRequestTestCase, create_organization, make_user_admin
from backend import errors
from phi.models import *
from rest_framework import status
from unittest.mock import patch
from user_auth.models import *

import json


class TestPlacesViewSet(UserRequestTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.initObjects()

    def test_create_checks_admin_permissions(self):
        "Should return 400 if user is not admin"
        new_place_name = 'place 2'
        new_contact_number = '987298743'
        payload = {
            "name": new_place_name,
            "contactNumber" : new_contact_number,
            "address": {
                "streetAddress": "Str 1",
                "zipCode": "534",
                "city": "NewBudlur",
                "state": "KA",
                "country": "India",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/'  # reverse('places-list')
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('django.conf.settings.PUBNUB')
    def test_creates_place_and_address(self, settings_mock):
        "Creates Place and address for correct request"
        make_user_admin(self.user_profile)
        user_org = UserOrganizationAccess.objects.get(user=self.user_profile)
        payload = {
            "name": "place_name",
            "contactNumber" : "contact_number",
            "address": {
                "streetAddress": "When you",
                "zipCode": "play the",
                "city": "game of thrones,",
                "state": "you either win",
                "country": "or you die",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/'  # reverse('places-list')
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        places = Place.objects.all()
        self.assertEqual(places.count(), 1)
        self.assertEqual(places[0].name, payload["name"])
        self.assertEqual(places[0].contact_number, payload["contactNumber"])
        addresses = Address.objects.all()
        self.assertEqual(addresses.count(), 1)
        self.validate_address_object_equal(addresses[0], payload["address"])
        settings_mock.publish.assert_called_with()
        channel_call_params = 'organisation_' + str(user_org.organization.uuid)
        settings_mock.publish().channel.assert_called_with(channel_call_params)
        message_call_params = {
            'actionType': 'CREATE_PLACE',
            'placeID': str(places[0].uuid)
        }
        settings_mock.publish().channel(channel_call_params).message.assert_called_with(message_call_params)

    @patch('django.conf.settings.PUBNUB')
    def test_creates_place_for_contact_number_null(self, settings_mock):
        "Creates place if contact number is null"
        make_user_admin(self.user_profile)
        user_org = UserOrganizationAccess.objects.get(user=self.user_profile)
        payload = {
            "name": "place_name",
            "contactNumber": None,
            "address": {
                "streetAddress": "When you run",
                "zipCode": "run the",
                "city": "unit tests",
                "state": "they either pass",
                "country": "or they fail",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/'  # reverse('places-list')
        response = self.client.post(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        places = Place.objects.all()
        self.assertEqual(places.count(), 1)
        self.assertEqual(places[0].name, payload["name"])
        self.assertIsNone(places[0].contact_number)
        addresses = Address.objects.all()
        self.assertEqual(addresses.count(), 1)
        self.validate_address_object_equal(addresses[0], payload["address"])
        settings_mock.publish.assert_called_with()
        channel_call_params = 'organisation_' + str(user_org.organization.uuid)
        settings_mock.publish().channel.assert_called_with(channel_call_params)
        message_call_params = {
            'actionType': 'CREATE_PLACE',
            'placeID': str(places[0].uuid)
        }
        settings_mock.publish().channel(channel_call_params).message.assert_called_with(message_call_params)

    def test_update_fails_if_user_is_not_admin(self):
        "Should fail if user is not admin"
        payload = {
            "name": "place_name",
            "contactNumber": None,
            "address": {
                "streetAddress": "When you run",
                "zipCode": "run the",
                "city": "unit tests",
                "state": "they either pass",
                "country": "or they fail",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/' + str(uuid.uuid4()) + '/' # reverse('places-detail', None, str(uuid.uuid4()))
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_fails_if_place_does_not_exist(self):
        "Should fail if requested place does not exist"
        make_user_admin(self.user_profile)
        payload = {
            "name": "place_name",
            "contactNumber": None,
            "address": {
                "streetAddress": "When you run",
                "zipCode": "run the",
                "city": "unit tests",
                "state": "they either pass",
                "country": "or they fail",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/' + str(uuid.uuid4()) + '/' # reverse('places-detail', None, str(uuid.uuid4()))
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'success': False,
            'error': errors.PLACE_NOT_EXIST
        }
        self.assertDictEqual(response.data, expected_response)

    @patch('django.conf.settings.PUBNUB')
    def test_update_updates_place_and_address(self, settings_mock):
        "Should update place and address objects"
        make_user_admin(self.user_profile)
        user_org = UserOrganizationAccess.objects.get(user=self.user_profile)
        place = self.createPlaceAndAddress()
        payload = {
            "name": "place_name",
            "contactNumber": "234",
            "address": {
                "streetAddress": "When you run",
                "zipCode": "run the",
                "city": "unit tests",
                "state": "they either pass",
                "country": "or they fail",
                "latitude": 354.4,
                "longitude": 23.55
            }
        }
        url = '/phi/v1.0/places/' + str(place.uuid) + '/'  # reverse('places-detail', None, str(uuid.uuid4()))
        response = self.client.put(url, json.dumps(payload), "application/json", **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        places = Place.objects.all()
        self.assertEqual(places.count(), 1)
        self.assertEqual(places[0].name, payload["name"])
        self.assertEqual(places[0].contact_number, payload["contactNumber"])
        self.validate_address_object_equal(places[0].address, payload["address"])
        settings_mock.publish.assert_called_with()
        channel_call_params = 'organisation_' + str(user_org.organization.uuid)
        settings_mock.publish().channel.assert_called_with(channel_call_params)
        message_call_params = {
            'actionType': 'UPDATE_PLACE',
            'placeID': str(places[0].uuid)
        }
        settings_mock.publish().channel(channel_call_params).message.assert_called_with(message_call_params)

    def test_retrieve_place_does_not_exist(self):
        "Should return 400 if place does not exist"
        url = '/phi/v1.0/places/' + str(uuid.uuid4()) + "/"
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'success': False,
            'error': errors.PLACE_NOT_EXIST
        }
        self.assertDictEqual(response.data, expected_response)

    def test_retrieve_place_does_not_belong_to_user_org(self):
        "Should return 400 if place exists but does not belong to user organization"
        place = self.createPlaceAndAddress()
        Place.objects.filter(uuid=place.uuid).update(organization=create_organization())
        url = '/phi/v1.0/places/' + str(place.uuid) + "/"
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_response = {
            'success': False,
            'error': errors.PLACE_NOT_EXIST
        }
        self.assertDictEqual(response.data, expected_response)

    def test_retrieve_place(self):
        "Should retrieve place"
        place = self.createPlaceAndAddress()
        url = '/phi/v1.0/places/' + str(place.uuid) + "/"
        response = self.client.get(url, **self.get_base_headers())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # TODO Replace with mocked object
        expected_response = {
            "placeID": str(place.uuid),
            "contactNumber": place.contact_number,
            "name": place.name,
            "address": {
                'addressID': str(place.address.uuid),
                'apartmentNo': place.address.apartment_no,
                'streetAddress': place.address.street_address,
                'zipCode': place.address.zip,
                'city': place.address.city,
                'state': place.address.state,
                'country': place.address.country,
                'latitude': place.address.latitude,
                'longitude': place.address.longitude
            }
        }
        self.assertDictEqual(response.data, expected_response)



    def createPlaceAndAddress(self):
        address = Address.objects.create(street_address="s_a", zip='234', city='Bangalore', state='state',
                                         country='country', latitude=23.3, longitude=34.3)
        return Place.objects.create(name='place', contact_number='123', address=address, organization=self.organization)

    def validate_address_object_equal(self, address_db_object, expected_value):
        self.assertEqual(address_db_object.street_address, expected_value["streetAddress"])
        self.assertEqual(address_db_object.zip, expected_value["zipCode"])
        self.assertEqual(address_db_object.city, expected_value["city"])
        self.assertEqual(address_db_object.state, expected_value["state"])
        self.assertEqual(address_db_object.country, expected_value["country"])
        self.assertAlmostEqual(address_db_object.latitude, expected_value["latitude"])
        self.assertAlmostEqual(address_db_object.longitude, expected_value["longitude"])