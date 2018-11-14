from backend import errors
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from phi import models
from phi.constants import NPI_DATA_URL
from phi.serializers.request_serializers import CreatePhysicianRequestSerializer
from phi.serializers.response_serializers import PhysicianResponseSerializer
from phi.views.utils import my_publish_callback
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from user_auth.models import UserOrganizationAccess

import logging
import requests

logger = logging.getLogger(__name__)


class PhysiciansViewSet(viewsets.ViewSet):
    model = models.Physician
    queryset = models.Physician.objects.all()
    permission_classes = (IsAuthenticated,)

    def parse_query_params(self, query_params):
        if not query_params:
            return None, None, None
        sort = query_params.get('sort', None)
        if sort:
            if getattr(self.model, sort, None):
                sort_field = sort
            else:
                sort_field = 'last_name'
        else:
            sort_field = 'last_name'
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        if size:
            try:
                size = int(size)
            except Exception as e:
                size = None
        return query, sort_field, size

    def get_results(self, initial_query_set, query, sort_field, size):
        queryset = initial_query_set
        if query:
            queryset = initial_query_set.filter(Q(first_name__istartswith=query) | Q(last_name__istartswith=query))
        if sort_field:
            queryset = queryset.order_by(sort_field)
        if size:
            queryset = queryset[:int(size)]
        return queryset

    def list(self, request):
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.get(user=user.profile, is_admin=True)
            query_params = request.query_params
            query, sort_field, size = self.parse_query_params(query_params)
            organization_physicians = models.Physician.objects.filter(organization=user_org.organization)
            physicians = self.get_results(organization_physicians, query, sort_field, size)
            serializer = PhysicianResponseSerializer(physicians, many=True)
            logger.debug(str(serializer.data))
            return Response(serializer.data)
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'error': errors.ACCESS_DENIED})

    def create(self, request):
        request_serializer = CreatePhysicianRequestSerializer(data=request.data.get('physician', None))
        if not request_serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
        try:
            user_org = UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            request_serializer.save(organization_id=user_org.organization.uuid)
            return Response(status=status.HTTP_201_CREATED, data={})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'error': errors.ACCESS_DENIED})

    def retrieve(self, request, pk=None):
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.get(user=user.profile,is_admin=True)
            physician = models.Physician.objects.get(uuid=pk, organization=user_org.organization)
            serializer = PhysicianResponseSerializer(physician)
            return Response(serializer.data)
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except models.Physician.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.PHYSICIAN_NOT_EXIST})

    def update(self, request, pk=None):
        try:
            user_org = UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
            physician = models.Physician.objects.get(uuid=pk, organization=user_org.organization)
            request_serializer = CreatePhysicianRequestSerializer(instance=physician, data=request.data)
            if not request_serializer.is_valid():
                return Response(status=status.HTTP_400_BAD_REQUEST, data=request_serializer.errors)
            episodes = models.Episode.objects.filter(primary_physician=physician)
            physician_patients = list(map(lambda episode: episode.patient, episodes))
            with transaction.atomic():
                request_serializer.save()
                for patient in physician_patients:
                    episode = patient.episodes.get(is_active=True)
                    user_episode_access_list = models.UserEpisodeAccess.objects.filter(episode=episode)
                    if user_episode_access_list.count() > 0:
                        users_linked_to_patient = [user_episode_access.user.uuid for user_episode_access in
                                                   user_episode_access_list]
                        for user_uuid in users_linked_to_patient:
                            settings.PUBNUB.publish().channel(str(user_uuid) + '_assignedPatients').message({
                                'actionType': 'UPDATE',
                                'patientID': str(patient.uuid),
                            }).async(my_publish_callback)
            return Response(status=status.HTTP_200_OK, data={})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'error': errors.ACCESS_DENIED})
        except models.Physician.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.PHYSICIAN_NOT_EXIST})

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
        # TODO Will be handled after checking with Gaurav
        # try:
        #     UserOrganizationAccess.objects.get(user=request.user.profile, is_admin=True)
        #     physician = models.Physician.objects.get(uuid=pk)
        #     with transaction.atomic():
        #         physician.delete()
        #         return Response(status=status.HTTP_200_OK, data={})
        # except UserOrganizationAccess.DoesNotExist:
        #     return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        # except models.Physician.DoesNotExist:
        #     return Response(status=status.HTTP_400_BAD_REQUEST,
        #                     data={'success': False, 'error': errors.PHYSICIAN_NOT_EXIST})


# Todo: Protect this API
def fetch_physician(request):
    npi_id = request.GET.get('npi_id', '')
    url = NPI_DATA_URL + str(npi_id) + '.json'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            logger.debug('Response: %s' % str(data))
            return JsonResponse(data)
        else:
            return JsonResponse({'success': False, 'error': 'Incorrect NPI Id'})
    except Exception as e:
        logger.error('Error in fetching Physician data using NPI ID. Error: %s' % str(e))
        return JsonResponse({'success': False, 'error': errors.UNKNOWN_ERROR})

