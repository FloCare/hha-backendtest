from backend import errors
from django.conf import settings
from django.db import transaction
from phi import models
from phi.serializers.request_serializers import CreatePlaceRequestSerializer
from phi.serializers.response_serializers import PlaceResponseSerializer
from phi.serializers.serializers import PlaceUpdateSerializer
from phi.views.utils import my_publish_callback
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_auth.models import UserOrganizationAccess
from user_auth.serializers import AddressSerializer

import logging

logger = logging.getLogger(__name__)


class PlacesViewSet(viewsets.ViewSet):
    model = models.Place
    queryset = models.Place.objects.all()
    permission_classes = (IsAuthenticated,)

    query_to_db_map = {
        'contactNumber': 'contact_number',
        'name': 'name'
    }

    def get_order_by_field(self, query_params):
        order = 'name'
        fields = models.Place._meta.fields
        fields_list = map(lambda field: field.name, fields)
        if 'sort' in query_params:
            sort_value = query_params['sort']
            if sort_value in self.query_to_db_map.keys() and self.query_to_db_map[sort_value] in fields_list:
                order = self.query_to_db_map[query_params['sort']]
                if 'order' in query_params and query_params['order'] == 'DESC':
                    order = '-' + order
        return order

    def create(self, request):
        request_serializer = CreatePlaceRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
        data = request_serializer.validated_data
        try:
            user_org = UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            address_serializer = AddressSerializer(data=request.data['address'])
            with transaction.atomic():
                address_serializer.is_valid()
                address_obj = address_serializer.save()
                place = models.Place.objects.create(name=data['name'], contact_number=data['contact_number'],
                                                    organization=user_org.organization, address=address_obj)
                settings.PUBNUB.publish().channel('organisation_' + str(user_org.organization.uuid)).message({
                    'actionType': 'CREATE_PLACE',
                    'placeID': str(place.uuid)
                }).async(my_publish_callback)
                return Response(status=status.HTTP_201_CREATED, data={})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})

    def update(self, request, pk=None):
        request_serializer = CreatePlaceRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
        try:
            user_org = UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            place = models.Place.objects.get(uuid=pk)
            place_serializer = PlaceUpdateSerializer(instance=place, data=request.data)
            address_serializer = AddressSerializer(instance=place.address, data=request.data['address'])
            with transaction.atomic():
                place_serializer.is_valid()
                place_serializer.save()
                address_serializer.is_valid()
                address_serializer.save()
                settings.PUBNUB.publish().channel('organisation_' + str(user_org.organization.uuid)).message({
                    'actionType': 'UPDATE_PLACE',
                    'placeID': str(place.uuid)
                }).async(my_publish_callback)
                return Response(status=status.HTTP_200_OK, data={})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except models.Place.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.PLACE_NOT_EXIST})

    def retrieve(self, request, pk=None):
        user = request.user
        try:
            user_org = UserOrganizationAccess.objects.get(user=user.profile)
            place = models.Place.objects.get(uuid=pk, organization=user_org.organization)
            return Response(status=status.HTTP_200_OK, data=PlaceResponseSerializer(place).data)
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except models.Place.DoesNotExist as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.PLACE_NOT_EXIST})

    def list(self, request):
        user = request.user
        try:
            user_org = UserOrganizationAccess.objects.get(user=user.profile)
            order_field = self.get_order_by_field(request.query_params)
            places = models.Place.objects.filter(organization=user_org.organization).order_by(order_field)
            return Response(status=status.HTTP_200_OK, data=PlaceResponseSerializer(places, many=True).data)
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})

    def destroy(self, request, pk=None):
        try:
            user_org = UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            # Todo: Add prefetch_related?
            place = models.Place.objects.get(uuid=pk)

            with transaction.atomic():
                place.soft_delete()
                settings.PUBNUB.publish().channel('organisation_' + str(user_org.organization.uuid)).message({
                    'actionType': 'DELETE_PLACE',
                    'placeID': str(pk)
                }).async(my_publish_callback)
                return Response(status=status.HTTP_200_OK, data={})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except models.Place.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.PLACE_NOT_EXIST})
