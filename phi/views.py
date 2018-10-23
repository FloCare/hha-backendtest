import dateutil.parser
from django.core.paginator import Paginator
from django.conf import settings
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend import errors
from phi import models
from phi.constants import query_to_db_field_map, NPI_DATA_URL, total_miles_buffer_allowed
from phi.serializers import OrganizationPatientMappingSerializer, \
    EpisodeSerializer, PatientPlainObjectSerializer, UserEpisodeAccessSerializer, PatientWithUsersSerializer, \
    PatientUpdateSerializer, VisitSerializer, PatientWithUsersAndPhysiciansSerializer, \
    VisitMilesSerializer, PlaceUpdateSerializer
from phi.exceptions.VisitsNotFoundException import VisitsNotFoundException
from phi.exceptions.TotalMilesDidNotMatchException import TotalMilesDidNotMatchException
from phi.response_serializers import PatientListSerializer, PatientDetailsResponseSerializer, \
    EpisodeDetailsResponseSerializer, VisitDetailsResponseSerializer, PhysicianResponseSerializer, \
    VisitResponseSerializer, PatientDetailsWithOldIdsResponseSerializer, VisitForOrgResponseSerializer, \
    ReportSerializer, ReportDetailSerializer, ReportDetailsForWebSerializer, PlaceResponseSerializer,\
    PatientsForOrgSerializer, AssignedPatientsHistorySerializer, PlaceHistoryResponseSerializer
from phi.request_serializers import CreatePlaceRequestSerializer, CreatePhysicianRequestSerializer
from user_auth.models import UserOrganizationAccess, Address
from user_auth.serializers import AddressSerializer
import logging
import datetime
import requests
import uuid
import traceback
from phi.forms import UploadFileForm

logger = logging.getLogger(__name__)


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        logger.info("# Message successfully published to specified channel.")
    else:
        logger.error("# NOT Message successfully published to specified channel.")
        # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];


class AccessiblePatientViewSet(viewsets.ViewSet):
    queryset = models.Patient.objects.all()
    permission_classes = (IsAuthenticated,)

    local_counter = 1

    @staticmethod
    def parse_data(data):
        try:
            patient = data['patient']
            address = patient.pop('address')
            physician = data.get('physicianId', None)
            if 'users' in data:
                users = data['users']
            else:
                users = []
            return patient, address, users, physician
        except Exception as e:
            logger.error('Incorrect or Incomplete data passed: %s' % str(e))
            return None, None, None, None

    def parse_query_params(self, query_params):
        if not query_params:
            return None, None
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        try:
            size = int(size)
        except Exception as e:
            size = None

        return query, size

    def get_results(self, initial_query_set, query, sort_field):
        queryset = initial_query_set
        if query:
            words = query.split()
            for word in words:
                queryset = initial_query_set.filter(Q(first_name__istartswith=word) | Q(last_name__istartswith=word))
        if sort_field:
            queryset = queryset.order_by(sort_field)
        return queryset

    def update(self, request, pk=None):
        """
        Update the users associated to this patient
        :param request:
        :param pk:
        :return:
        """
        try:
            data = request.data
            users = data.get('users', [])
            physician = data.get('physicianId', None)

            # Check if caller is an admin
            user_org = UserOrganizationAccess.objects.filter(user=request.user.profile).get(is_admin=True)
            if user_org:
                organization = user_org.organization

                # Check if the passed users belong to this organization
                # Someone might maliciously pass invalid users
                users_count = UserOrganizationAccess.objects.filter(organization=organization).filter(user_id__in=users).count()
                if len(users) != users_count:
                    raise Exception('Invalid user passed')

                patient = models.Patient.objects.get(uuid=pk)

                try:
                    # Get the active Episode ID for this patient
                    episode = patient.episodes.get(is_active=True)
                    episode_id = episode.uuid
                except Exception as e:
                    logger.error('Error in fetching active episode: %s' % str(e))
                    raise e

                logger.debug('org-id: %s' % str(organization.uuid))
                logger.debug('patient-id: %s' % str(patient.uuid))

                # Check if org has access to this patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization=organization).filter(patient_id=patient.uuid)
                if org_has_access.exists():
                    with transaction.atomic():
                        # Update patient fields if present
                        if data.get('patient'):
                            try:
                                value = data['patient']['dob']
                                d = dateutil.parser.parse(value)
                                data['patient']['dob'] = d.strftime('%Y-%m-%d')
                            except KeyError as e:
                                # Key is not present
                                logger.warning('Key is not present: %s' % str(e))
                            patient_obj = models.Patient.objects.get(uuid=data['id'])
                            serializer = PatientUpdateSerializer(patient_obj, data=data['patient'], partial=True)
                            serializer.is_valid()
                            serializer.save()

                        # Attach Physicians Passed to this Episode
                        if physician:
                            episode.primary_physician_id = physician
                            episode.save()

                        # Add the users sent in the payload
                        for user_id in users:
                            try:
                                models.UserEpisodeAccess.objects \
                                    .get(organization=organization, episode_id=episode_id, user_id=user_id)
                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'actionType': 'UPDATE',
                                    'patientID': str(patient.uuid),
                                }).async(my_publish_callback)
                            except models.UserEpisodeAccess.DoesNotExist as e:
                                logger.warning(str(e))
                                try:
                                    # Check if UserEpisodeAccess entry exists and is_deleted, if yes, mark undelete
                                    access = models.UserEpisodeAccess.all_objects.exclude(deleted_at=None).get(organization=organization, episode_id=episode_id, user_id=user_id)
                                    access.deleted_at = None
                                    access.save()
                                except models.UserEpisodeAccess.DoesNotExist as e:
                                    logger.warning(str(e))

                                    access_serializer = UserEpisodeAccessSerializer(
                                        data={
                                            'organization_id': organization.uuid,
                                            'user_id': user_id,
                                            'episode_id': episode_id,
                                            'user_role': 'CareGiver'
                                        })
                                    access_serializer.is_valid()
                                    access_serializer.save()
                                    logger.debug('new episode access created for userid: %s' % str(user_id))

                                # SILENT NOTIFICATION
                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'actionType': 'ASSIGN',
                                    'patientID': str(patient.uuid),
                                    'pn_apns': {
                                        "aps": {
                                            "content-available": 1
                                        },
                                        "payload": {
                                            "messageCounter": AccessiblePatientViewSet.local_counter,
                                            "patientID": str(patient.uuid)
                                        },
                                    },
                                    'pn_gcm': {
                                        'data': {
                                            'notificationBody': "You have a new Patient",
                                            "sound": "default",
                                            "navigateTo": 'patient_list',
                                            'messageCounter': AccessiblePatientViewSet.local_counter,
                                            'patientID': str(patient.uuid)
                                        }
                                    }
                                }).async(my_publish_callback)

                                # NOISY NOTIFICATION
                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'pn_apns': {
                                        "aps": {
                                            "alert": {
                                                "body": "You have a new Patient",
                                            },
                                            "sound": "default",
                                        },
                                        "payload": {
                                            "messageCounter": AccessiblePatientViewSet.local_counter,
                                            "patientID": str(patient.uuid),
                                            "navigateTo": 'patient_list'
                                        }
                                    }
                                }).async(my_publish_callback)

                        user_access_to_delete = models.UserEpisodeAccess.objects.filter(
                            organization=organization).filter(episode_id=episode_id).exclude(user_id__in=users)
                        logger.debug('to delete: %s' % str(user_access_to_delete))

                        for user_episode_access in user_access_to_delete.iterator():
                            user_id = user_episode_access.user_id
                            logger.debug('User Access to delete: %s' % str(user_episode_access))

                            user_episode_access.soft_delete()

                            settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': str(patient.uuid),
                            }).async(my_publish_callback)
                            # Also send out User-Unassigned Msg to that episode's channel
                            settings.PUBNUB.publish().channel('episode_' + str(episode_id)).message({
                                'actionType': 'USER_UNASSIGNED',
                                'userID': str(user_id),
                            }).async(my_publish_callback)

                            try:
                                # Hard delete future visits for that user
                                logger.debug('Deleting visits for this user: %s' % str(user_id))
                                # Get midNightEpoch for today
                                today_midnight_epoch = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000
                                future_visits = models.Visit.objects.filter(episode_id=episode_id).filter(user_id=user_id).filter(is_done=False).filter(midnight_epoch__gte=today_midnight_epoch)
                                future_visits.delete()
                                logger.debug('%s Visits deleted successfully' % str(len(future_visits)))
                            except Exception as e:
                                logger.warning('Could not delete visits for user_id: %s, episode_id: %s. Error: %s' % (str(user_id), str(episode_id), str(e)))

                        AccessiblePatientViewSet.local_counter += 1
                    return Response({'success': True})

            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def destroy(self, request, pk=None):
        """
        Soft Delete the patient, if user has access to it.
        :param request:
        :param pk:
        :return:
        """
        # Delete Patient and its related entities
        try:
            user = request.user
            # Check if user is admin of this org
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            organization = user_org.organization
            if user_org:
                patient = models.Patient.objects.prefetch_related('episodes').get(uuid=pk)
                episode_ids = patient.episodes.all().filter(is_active=True).values_list('uuid', flat=True)

                # Org has access to patient
                try:
                    user_episode_accesses = models.UserEpisodeAccess.objects.filter(organization=organization).filter(episode_id__in=episode_ids)
                    user_ids = [access.user.uuid for access in user_episode_accesses]

                    with transaction.atomic():
                        # Soft delete ALL the related entities
                        patient.soft_delete()

                        for user_id in user_ids:
                            settings.PUBNUB.publish().channel(
                                str(user_id) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': str(patient.uuid),
                            }).async(my_publish_callback)

                    logger.info('Delete successful')
                    return Response({'success': True, 'error': None})
                except models.OrganizationPatientsMapping.DoesNotExist:
                    logger.info('Org does not have %s access to this patient: %s' % (organization.uuid, patient.uuid))
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def retrieve(self, request, pk=None):
        """
        Return the details of this patient, if user has access to it.
        :param request:
        :param pk:
        :return:
        """
        # Check if user is admin of this org
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            organization = user_org.organization
            if user_org :
                patient = models.Patient.objects.get(uuid=pk)

                # Assumption: A patient can only have 1 active episode at a time
                # Get the active episodes for that patient
                episode = patient.episodes.get(is_active=True)
                physician_id = None
                if episode.primary_physician:
                    physician_id = episode.primary_physician.uuid

                # Org has access to patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization=organization).filter(patient=patient)
                if org_has_access.exists():
                    user_profile_ids = models.UserEpisodeAccess.objects.filter(episode_id=episode.uuid).filter(organization=organization).values_list('user_id', flat=True)
                    serializer = PatientWithUsersAndPhysiciansSerializer({'id': patient.uuid, 'patient': patient, 'userIds': list(user_profile_ids), 'physicianId': physician_id})
                    return Response(serializer.data)
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def filter_user_ep_objects_by_episode_ids(self, user_ep_objects, episode_ids):
        return [user_ep_object for user_ep_object in user_ep_objects if user_ep_object.episode.uuid in episode_ids]

    def get_episode_ids_for_patient(self, patient):
        return list(map(lambda episode: episode.uuid, patient.episodes.all()))

    def get_user_ids_for_patient(self, patient, all_user_ep_access_objects):
        episode_ids = self.get_episode_ids_for_patient(patient)
        filtered_user_ep_objects = self.filter_user_ep_objects_by_episode_ids(all_user_ep_access_objects, episode_ids)
        return list(map(lambda object: object.user.uuid, filtered_user_ep_objects))

    # Todo: also send the active episodeId with each patient
    def list(self, request):
        """
        Return list of details of patients this user has access to.
        :param request:
        :return:
        """
        try:
            user = request.user

            # Todo: Improve Sorting logic - use DRF builtin
            query_params = request.query_params
            sort_field = 'last_name'
            per_page = None
            page = 1
            order = 'ASC'
            if 'sort' in query_params:
                sort_field = query_to_db_field_map.get(query_params['sort'], sort_field)
                if 'order' in query_params:
                    order = query_params['order']
            if order == 'DESC':
                sort_field = '-' + sort_field
            if 'page' in query_params:
                page = query_params.get('page', None)
            if 'perPage' in query_params:
                per_page = query_params.get('perPage', None)

            # Check if this user is admin of the org
            # Note: (A user can be admin of only 1 org)
            try:
                user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
                if user_org :
                    logger.debug('User is admin: %s' % str(user))
                    query_params = request.query_params
                    query, size = self.parse_query_params(query_params)
                    patient_ids = models.OrganizationPatientsMapping.objects.filter(organization=user_org.organization).values_list('patient_id')
                    patients = models.Patient.objects.select_related('address').prefetch_related('episodes').filter(uuid__in=patient_ids)
                    if per_page is not None:
                        paginator = Paginator(self.get_results(patients, query, sort_field), per_page)
                        patients = paginator.page(page)
                    episode_id_list = [[episode.uuid for episode in list(patient.episodes.all())] for patient in patients]
                    episode_id_list = [item for sublist in episode_id_list for item in sublist]
                    user_episode_access_objects = models.UserEpisodeAccess.objects.filter(episode_id__in=episode_id_list, organization=user_org.organization)
                    patient_list = list(map(lambda patient: {
                        'patient': patient,
                        'userIds': self.get_user_ids_for_patient(patient, user_episode_access_objects)
                    }, patients))
                    serializer = PatientWithUsersSerializer(patient_list, many=True)
                    response = Response(serializer.data)
                    # Custom header being sent as part of response and being whitelisted
                    if per_page is not None:
                        response['content-range'] = paginator.count
                        response['Access-Control-Expose-Headers'] = "content-range"
                    return response
            except Exception as e:
                logger.error('User is not admin: %s' % str(e))
                logger.error(traceback.format_exc())
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

        #     # Todo: Don't go to this part of the API ???
        #     # Check if user has episodes to his name
        #     print('User is not admin')                      # This part of API not being used currently
        #     # TODO: ALSO CHECK REQUEST USER'S ORGANIZATION
        #     episode_ids = list(models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).values_list('episode_id', flat=True))  # noqa
        #     patients = list()
        #     for episode_id in episode_ids:
        #         patients.append(models.Episode.objects.get(id=episode_id).patient)
        #     serializer = PatientSerializerWeb(patients, many=True)
        #     return Response(serializer.data)
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def create(self, request, format=None):
        """
        Within Single Transaction:
            check if the calling user is an admin of this org
            check if the passed users belong to this org
            Add address
            patient
            episode
            link patient to org
            link episode to user
        :param request:
        :param format:
        :return:
        """
        user = request.user
        data = request.data
        patient, address, users, physicianId = AccessiblePatientViewSet.parse_data(data)
        if (not patient) or (not address):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
        try:
            # Find this user's organization and Check if this user is the admin
            # Only admin should have write permissions
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            organization = user_org.organization

            # Check if the passed users belong to this organization
            # Someone might maliciously pass invalid users
            # TODO: This IS BAAAAD. Change this ASAP to bulk API.
            for userid in users:
                u = UserOrganizationAccess.objects.filter(organization=organization).get(user_id=userid)
                if not u:
                    raise Exception('Invalid user passed')

            if physicianId:
                if not models.Physician.objects.filter(pk=physicianId).exists():
                    logger.debug('PhysicianId is: invalid')
                    raise Exception('Invalid physician passed')

            with transaction.atomic():
                # Save Address
                logger.debug('ADdress is: %s' % str(address))
                serializer = AddressSerializer(data=address)
                serializer.is_valid()
                address_obj = serializer.save()
                logger.debug('Address object is: %s' % str(address_obj))

                try:
                    value = patient['dob']
                    d = dateutil.parser.parse(value)
                    patient['dob'] = d.strftime('%Y-%m-%d')
                except KeyError as e:
                    # Key is not present
                    logger.warning('Key is not present: %s' % str(e))

                # # Save Patient
                patient['address_id'] = address_obj.uuid
                logger.debug('Patient data is: %s' % str(patient))
                patient_serializer = PatientPlainObjectSerializer(data=patient)
                patient_serializer.is_valid()
                patient_obj = patient_serializer.save()
                logger.debug('Patient object saved successfully: %s' % str(patient_obj))

                # Save Episode
                episode = {
                    'patient': patient_obj.uuid,
                    'socDate': patient.get('soc_date') or None,
                    'endDate': patient.get('end_date') or None,
                    'period': patient.get('period') or None,
                    'cprCode': patient.get('cpr_code') or None,
                    'transportationLevel': patient.get('transportation_level') or None,
                    'acuityType': patient.get('acuity_type') or None,
                    'classification': None,
                    'allergies': None,
                    'pharmacy': None,
                    'socClinician': None,
                    'attendingPhysician': None,
                    'primaryPhysician': physicianId
                }
                logger.debug('Saving episode: %s' % str(episode))
                episode_serializer = EpisodeSerializer(data=episode)
                episode_serializer.is_valid()
                episode_obj = episode_serializer.save()
                logger.debug('Episode Object saved successfully: %s' % str(episode_obj))
                logger.debug('Episode Object saved successfully: %s' % episode_obj.primary_physician)

                # Link Patient to Org
                mapping_serializer = OrganizationPatientMappingSerializer(data={'organization_id': organization.uuid,
                                                                                'patient_id': patient_obj.uuid})
                mapping_serializer.is_valid()
                mapping_serializer.save()
                logger.debug('Mapping object saved successfully: %s' % str(mapping_serializer.validated_data))

                logger.debug('Saving USerEpisodeAccess Serializer')
                # Link Episode to Users passed
                # Todo: Do a bulk update
                for user_id in users:
                    access_serializer = UserEpisodeAccessSerializer(data={'organization_id': organization.uuid,
                                                                          'user_id': user_id,
                                                                          'episode_id': episode_obj.uuid,
                                                                          'user_role': 'CareGiver'})
                    access_serializer.is_valid()
                    access_serializer.save()
                    logger.debug('UserEpisodeAccess saved successfully')

                    settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                        'actionType': 'ASSIGN',
                        'patientID': str(patient_obj.uuid),
                        'pn_apns': {
                            "aps": {
                                "content-available": 1
                            },
                            "payload": {
                                "messageCounter": AccessiblePatientViewSet.local_counter,
                                "patientID": str(patient_obj.uuid)
                            }
                        }
                    }).async(my_publish_callback)

                    settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                        'pn_apns': {
                            "aps": {
                                "alert": {
                                    "body": "You have a new Patient",
                                },
                                "sound": "default",
                            },
                            "payload": {
                                "messageCounter": AccessiblePatientViewSet.local_counter,
                                "patientID": str(patient_obj.uuid),
                                "navigateTo": 'patient_list'
                            }
                        },
                        'pn_gcm': {
                            'data': {
                                'notificationBody': "You have a new Patient",
                                "sound": "default",
                                "navigateTo": 'patient_list',
                                'messageCounter': AccessiblePatientViewSet.local_counter,
                                'patientID': str(patient_obj.uuid)
                            }
                        }
                    }).async(my_publish_callback)

                return Response({'success': True, 'error': None})

        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


class BulkCreatePatientView(APIView):
    permission_classes = (IsAuthenticated,)

    def create_episode(self, episode_data):
        logger.info('Saving episode: %s' % str(episode_data))
        episode_serializer = EpisodeSerializer(data=episode_data)
        episode_serializer.is_valid()
        episode_serializer.save()

    def post(self, request):
        data = request.data
        user = request.user
        try:
            user_org = UserOrganizationAccess.objects.get(user=user.profile)
            organization = user_org.organization
            success_counter = 0
            for patient_item in data:
                with transaction.atomic():
                    patient, address, users, physician_id = AccessiblePatientViewSet.parse_data(patient_item)
                    if not patient:
                        logger.info('patient key not present. Skipping create')
                        continue
                    patient_id = patient.get('patientID', None)
                    if patient_id and models.Patient.all_objects.filter(uuid=patient_id).exists():
                        logger.info('Patient exists. Skipping create')
                        continue
                    if physician_id:
                        if not models.Physician.objects.filter(uuid=physician_id).exists():
                            logger.warning('PhysicianId Does not exist. Skipping create')
                    logger.info('address')
                    logger.info(address)
                    address_serializer = AddressSerializer(data=address)
                    if not address_serializer.is_valid():
                        logger.warning(address_serializer.errors)
                    address_obj = address_serializer.save()
                    patient['address_id'] = address_obj.uuid
                    patient_serializer = PatientPlainObjectSerializer(data=patient)
                    if not patient_serializer.is_valid():
                        logger.warning(patient_serializer.errors)
                    patient_obj = patient_serializer.save()

                    episode = {
                        'patient': patient_obj.uuid,
                        'socDate': patient.get('soc_date') or None,
                        'endDate': patient.get('end_date') or None,
                        'period': patient.get('period') or None,
                        'cprCode': patient.get('cpr_code') or None,
                        'transportationLevel': patient.get('transportation_level') or None,
                        'acuityType': patient.get('acuity_type') or None,
                        'classification': None,
                        'allergies': None,
                        'pharmacy': None,
                        'socClinician': None,
                        'attendingPhysician': None,
                        'primaryPhysician': physician_id
                    }
                    episode_id = patient.get('episodeID', None)
                    if episode_id:
                        episode['id'] = episode_id
                        try:
                            # Should be dummy patient - Replace the dummy with new patient
                            # TODO Delete this hack code
                            episode = models.Episode.all_objects.get(uuid=episode_id)
                            old_patient = episode.patient
                            episode.patient_id = patient_obj.uuid
                            episode.save()
                            op_mappings = models.OrganizationPatientsMapping.all_objects.filter(patient_id=old_patient.uuid)
                            op_mappings.update(patient_id=patient_obj.uuid)
                            old_patient.delete()
                            success_counter += 1
                            continue
                        except models.Episode.DoesNotExist:
                            pass
                    self.create_episode(episode)
                    mapping_serializer = OrganizationPatientMappingSerializer(data={'organization_id': organization.uuid,
                                                                                    'patient_id': patient_obj.uuid})
                    mapping_serializer.is_valid()
                    mapping_serializer.save()
                    is_deleted = patient.get('archived', False)
                    if is_deleted:
                        patient_obj.soft_delete()
                    success_counter += 1
            return Response(status=status.HTTP_200_OK, data={'success': success_counter})
        except UserOrganizationAccess.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.USER_NOT_EXIST})


# Being Used for app API
class AccessiblePatientListView(generics.ListAPIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Todo: Also pass Organization for filtering
        accesses = models.UserEpisodeAccess.objects.filter(user=user.profile)
        patient_ids = [access.episode.patient.uuid for access in accesses]
        return patient_ids

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(data={'patients': queryset})
        serializer.is_valid()
        return Response(serializer.validated_data)


# Being used for app API
class AccessiblePatientsDetailView(APIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientDetailsResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'patientIDs' in data:
            patient_list = data['patientIDs']

            success_ids = list()
            failure_ids = list()
            for patient_id in patient_list:
                try:
                    episode = models.Patient.objects.get(uuid=patient_id).episodes.get(is_active=True)
                    access = models.UserEpisodeAccess.objects.filter(user=user.profile).filter(episode=episode)
                    if access.exists():
                        success_ids.append(patient_id)
                    else:
                        failure_ids.append(patient_id)
                except Exception as e:
                    logger.error(str(e))
                    failure_ids.append(patient_id)
            return success_ids, failure_ids
        return None, None

    def get_objects_by_ids(self, ids):
        # These patients exist, along-with 1 active episode
        patients = models.Patient.objects.filter(uuid__in=ids)
        return patients

    def post(self, request):
        success_ids, failure_ids = self.get_results(request)
        success = self.get_objects_by_ids(success_ids)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = self.serializer_class(resp)
        return Response(serializer.data)


# Todo: Temporary EndPoint to support migrating apps from 0.2.0 to Next Version
class GetPatientsByOldIds(APIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientDetailsWithOldIdsResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'patientIDs' in data:
            patient_list = data['patientIDs']

            success_ids = list()
            failure_ids = list()
            for patient_id in patient_list:
                try:
                    # Todo: Security Hazard. Returning any patient asked for.
                    patient = models.Patient.objects.filter(id=patient_id) #.episodes.get(is_active=True)
                    # access = models.UserEpisodeAccess.objects.filter(user=user.profile).filter(episode=episode)
                    # if access.exists():
                    if patient.exists():
                        success_ids.append(patient_id)
                    # else:
                    #     failure_ids.append(patient_id)
                except Exception as e:
                    logger.error(str(e))
                    failure_ids.append(patient_id)
            return success_ids, failure_ids
        return None, None

    def get_objects_by_ids(self, ids):
        # These patients exist, along-with 1 active episode
        patients = models.Patient.objects.filter(id__in=ids)
        return patients

    def post(self, request):
        success_ids, failure_ids = self.get_results(request)
        success = self.get_objects_by_ids(success_ids)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = self.serializer_class(resp)
        return Response(serializer.data)


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


def handle_uploaded_file(f, filename):
    with open(settings.MEDIA_ROOT + str(filename) + '.csv', 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return


def upload_file(request):
    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                filename = form.data['title']
                handle_uploaded_file(request.FILES['file'], filename)
                return JsonResponse({'success': True, 'msg': 'File uploaded successfully'})
            else:
                return JsonResponse({'success': False, 'msg': 'Form not valid'})
        else:
            form = UploadFileForm()
        return render(request, 'upload.html', {'form': form})
    else:
        raise Http404('Page does not exist')


class EpisodeView(APIView):
    queryset = models.Episode.objects.all()
    serializer_class = EpisodeDetailsResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'episodeIDs' in data:
            episode_list = data['episodeIDs']

            success_ids = list()
            failure_ids = list()
            for episode_id in episode_list:
                try:
                    episode = models.Episode.objects.filter(uuid=episode_id).get(is_active=True)
                    access = models.UserEpisodeAccess.objects.filter(user=user.profile).filter(episode=episode)
                    if access.exists():
                        success_ids.append(episode_id)
                    else:
                        failure_ids.append(episode_id)
                except Exception as e:
                    logger.error(str(e))
                    failure_ids.append(episode_id)
            return success_ids, failure_ids
        return None, None

    def get_objects_by_ids(self, ids):
        # These episodes exist and are active
        episodes = models.Episode.objects.filter(uuid__in=ids)
        return episodes

    def post(self, request):
        success_ids, failure_ids = self.get_results(request)
        success = self.get_objects_by_ids(success_ids)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = self.serializer_class(resp)
        return Response(serializer.data)


class GetMyVisits(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = VisitResponseSerializer

    def get(self, request):
        user = request.user.profile
        try:
            # Todo: Can check in UserEpisodeAccess, and only return visits for episodes user currently has access to
            visits = models.Visit.objects.select_related("visit_miles", "report_item", "report_item__report").filter(user=user)
            serializer = self.serializer_class(visits, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error('Error in fetching visits for this user: %s' % str(user))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


class GetVisitsByOrg(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = VisitForOrgResponseSerializer

    def get(self, request, date):
        user = request.user.profile
        try:
            user_org = UserOrganizationAccess.objects.filter(user=user).get(is_admin=True)
            midnight_epoch = int(datetime.datetime.strptime(date, "%Y-%m-%d").date().strftime('%s'))*1000
            visits = models.Visit.objects.filter(organization=user_org.organization).filter(midnight_epoch=midnight_epoch)
            serializer = self.serializer_class(visits, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error('Error in fetching visits for this org: %s' % str(user_org.organization))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


class GetVisitsView(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = VisitDetailsResponseSerializer

    def get_results(self, request):
        data = request.data
        if 'visitIDs' in data:
            visit_ids = data['visitIDs']
            try:
                # Allow users to query all visits from the same Org
                orgs = UserOrganizationAccess.objects.filter(user=request.user.profile).values_list('organization',
                                                                                                    flat=True)
                visit_objects = models.Visit.objects.filter(organization__in=orgs, id__in=visit_ids)
                success = list(visit_objects)
                success_ids = list(map(lambda visit: str(visit.id), visit_objects))
            except Exception as e:
                logger.error('Error in fetching visits data: %s' % str(e))
                success_ids = list()
            failure_ids = list(set(visit_ids) - set(success_ids))
            return success, failure_ids
        return None, None

    def post(self, request):
        success, failure_ids = self.get_results(request)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = self.serializer_class(resp)
        return Response(serializer.data)


class AddVisitsView(APIView):
    """
    Create multiple visits for a user.
    Only a user with access to an episode can create visit for that episode.
    Return a per visit success/failure response
    """
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)

    # Doing this from the app
    # Trigger notifications to other users with visits on same day for same episode
    # def publish_events(self, visit_id, episode_id):
    #     logger.debug('Events being published for visit_id: %s' % str(visit_id))
    #     return

    def create_dummy_patient_and_episode(self, user_profile, episode_id):
        address = Address.objects.create()
        patient = models.Patient.objects.create(first_name='Dummy',last_name='Patient',title='Mr', address=address)
        user_org = UserOrganizationAccess.objects.get(user=user_profile)
        mapping_serializer = OrganizationPatientMappingSerializer(data={'organization_id': user_org.organization.uuid,
                                                                        'patient_id': patient.uuid})
        mapping_serializer.is_valid()
        mapping_serializer.save()
        episode = {
            'id': episode_id,
            'patient': patient.uuid,
            'socDate': None,
            'endDate': None,
            'period': None,
            'cprCode': None,
            'transportationLevel': None,
            'acuityType': None,
            'classification': None,
            'allergies': None,
            'pharmacy': None,
            'socClinician': None,
            'attendingPhysician': None,
            'primaryPhysician': None
        }
        episode_serializer = EpisodeSerializer(data=episode)
        episode_serializer.is_valid()
        episode_serializer.save()
        logger.debug('Created Dummy patient and episode')

    def create_dummy_place(self, user_profile, place_id):
        address = Address.objects.create()
        user_org = UserOrganizationAccess.objects.get(user=user_profile)
        models.Place.objects.create(uuid=place_id, name='Dummy Place',organization=user_org.organization, address=address)
        logger.info('Created Dummy place ')

    def handle_missing_episode(self, visit, user_profile, payload):
        episode_id = visit.get('episodeID')
        if episode_id:
            try:
                models.Episode.all_objects.get(uuid=episode_id)
            except models.Episode.DoesNotExist:
                logger.debug('Episode Does not exist. Creating Dummy patient for payload: ')
                logger.debug(payload)
                self.create_dummy_patient_and_episode(user_profile, episode_id)

    def handle_missing_place(self, visit, user_profile, payload):
        place_id = visit.get('placeID')
        if place_id:
            try:
                models.Place.all_objects.get(uuid=place_id)
            except models.Place.DoesNotExist:
                logger.debug('Place Does not exist. Creating Dummy place for payload: ')
                logger.debug(payload)
                self.create_dummy_place(user_profile, place_id)

    def post(self, request):
        # Check user permissions for that episode
        user = request.user
        visits = request.data.get('visits')
        if not visits:
            logger.error('"visits" not present in request')
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})

        success = list()
        failure = list()

        # Check permission for, validate and save each visit
        for visit in visits:
            # Todo: Handle case of same-user-multiple-orgs
            try:
                org = UserOrganizationAccess.objects.get(user=request.user.profile).organization
            except UserOrganizationAccess.DoesNotExist as e:
                logger.warning('Not saving visit. Error: %s' % str(e))
                failure.append(visit)
                continue
            # TODO - remove this - only temporary fix
            # https://flocare.atlassian.net/browse/FC-115phi/response_serializers.py
            self.handle_missing_episode(visit, user.profile, request.data)
            self.handle_missing_place(visit, user.profile, request.data)

            serializer = VisitSerializer(data=visit)
            visit_miles = visit.get('visitMiles', {})
            visit_miles_serializer = VisitMilesSerializer(data=visit_miles)
            if serializer.is_valid() and visit_miles_serializer.is_valid():
                try:
                    visit_obj = serializer.save(user=request.user.profile, organization=org)
                    visit_miles_serializer.save(visit=visit_obj)
                    visit_id = serializer.validated_data.get('id')
                    success.append(visit_id)
                    # self.publish_events(visit_id, episode_id)
                except Exception as e:
                    logger.error('Error in saving visit: %s' % str(e))
                    failure.append(serializer.initial_data)
            else:
                logger.warning('Not saving. Invalid data received for visit: %s' % str(visit))
                failure.append(serializer.initial_data)
        logger.debug('Success: %s, Failure: %s' % (str(success), str(failure)))
        return Response({'success': success, 'failure': failure})


class UpdateVisitView(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'visitID' in data:
            visit_id = data['visitID']
            try:
                # Visit should belong to that user
                visit = models.Visit.objects.filter(user=user.profile).get(pk=visit_id)
                return visit
            except Exception as e:
                logger.error('Visit not found: %s' % (str(e)))
        return None

    def put(self, request):
        visit = self.get_results(request)
        if not visit:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.VISIT_NOT_EXIST})

        # Todo: Handle case of same-user-multiple-orgs
        # Get organization of requesting user
        try:
            org = UserOrganizationAccess.objects.get(user=request.user.profile).organization
        except UserOrganizationAccess.DoesNotExist as e:
            logger.error('Not saving visit. Error: %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': 'User has no organisation'})

        serializer = VisitSerializer(instance=visit, data=request.data)
        visit_miles = request.data.get('visitMiles', {})
        visit_miles_serialised_object = VisitMilesSerializer(instance=visit.visit_miles, data=visit_miles)

        if not (serializer.is_valid() and visit_miles_serialised_object.is_valid()):
            logger.error(str(serializer.errors))
            logger.error(str(visit_miles_serialised_object.errors))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        try:
            serializer.save(user=request.user.profile, organization=org)
            visit_miles_serialised_object.save()
        except IntegrityError as e:
            logger.error('IntegrityError. Cannot update visit: %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        except Exception as e:
            logger.error('Cannot update visit: %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        return Response({'success': True, 'error': None})


# Todo: When an episode access is removed, deleteAPI is also fired to corresponding remove visits.
# Todo: What if network call fails. Should the visits be deleted directly from server?
class DeleteVisitView(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_results(self, request):
        user = request.user
        data = request.data
        if 'visitIDs' in data:
            visit_ids = data['visitIDs']
            try:
                visit_objects = models.Visit.objects.filter(user=user.profile, id__in=visit_ids)
                if visit_objects.exists():
                    success_ids = list(map(lambda visit: str(visit.id), visit_objects))
                    # Todo: Should use bulk delete
                    [visit.soft_delete() for visit in visit_objects]
                else:
                    logger.error("These visits don't exist for this user")
                    success_ids = list()
            except Exception as e:
                logger.error('Error in deleting visits: %s' % str(e))
                success_ids = list()
            failure_ids = list(set(visit_ids) - set(success_ids))
            return success_ids, failure_ids
        return None, None

    def delete(self, request):
        success_ids, failure_ids = self.get_results(request)
        if (not success_ids) and (not failure_ids):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        return Response({'success': success_ids, 'failure': failure_ids})


class CreateReportForVisits(APIView):
    permission_classes = (IsAuthenticated,)

    def get_report_item_object(self, report, report_item, visits_map):
        visit = visits_map[uuid.UUID(report_item['visitID'])]
        return models.ReportItem(uuid=report_item['reportItemId'], report=report, visit=visit)

    def post(self, request):
        user = request.user
        data = request.data
        report_items = data['reportItems']
        report_id = data['reportID']
        logger.info('Payload for create report : %s' % str(data))
        total_miles_in_app_report = data['totalMiles']
        try:
            existing_report = models.Report.objects.get(uuid=report_id)
            existing_report_items = existing_report.report_items
            report_item_ids_in_db = list(existing_report_items.values_list("uuid", flat=True))
            report_item_ids = list(map((lambda item: uuid.UUID(item['reportItemId'])), report_items))
            if set(report_item_ids_in_db) == set(report_item_ids):
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_409_CONFLICT)
        except models.Report.DoesNotExist:
            response_data = {}
            try:
                with transaction.atomic():
                    report = models.Report(uuid=report_id, user=user.profile)
                    report.save()
                    visit_ids = list(map(lambda item : uuid.UUID(item['visitID']), report_items))
                    visits = models.Visit.all_objects.select_related('visit_miles').in_bulk(visit_ids, field_name="id")
                    visit_ids_in_db = visits.keys()
                    missing_visit_ids = list(set(visit_ids) - set(visit_ids_in_db))
                    if len(missing_visit_ids) > 0:
                        response_data = {'missingVisitIDs': missing_visit_ids}
                        raise VisitsNotFoundException(missing_visit_ids)
                    total_miles_travelled = 0
                    for visit_id in visits:
                        visit_miles = visits[visit_id].visit_miles
                        if visit_miles and visit_miles.odometer_start is not None and visit_miles.odometer_end is not None:
                            total_miles_travelled += visit_miles.odometer_end - visit_miles.odometer_start
                    difference_in_db_and_app = abs(total_miles_travelled - total_miles_in_app_report)
                    if difference_in_db_and_app > total_miles_buffer_allowed:
                        raise TotalMilesDidNotMatchException(total_miles_in_app_report, total_miles_travelled)
                    report_items = [self.get_report_item_object(report, report_item, visits) for report_item in report_items]
                    models.ReportItem.objects.bulk_create(report_items)
                return Response(status=status.HTTP_201_CREATED)
            except VisitsNotFoundException as e:
                logger.error('Visits Not Found Exception raised : %s', str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)
            except TotalMilesDidNotMatchException as e:
                logger.error('Total Miles Did not match exception raised %s', str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)


class GetReportsForUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        reports = models.Report.objects.filter(user=request.user.profile)
        reports_serializer = ReportSerializer(reports, many=True)
        return Response(status=status.HTTP_200_OK, data=reports_serializer.data)


class GetReportsDetailByIDs(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data
        report_ids = data['reportIDs']
        try:
            reports = models.Report.objects.prefetch_related("report_items__visit").in_bulk(report_ids, field_name='uuid').values()
            response = list(map((lambda report : {'report': report, 'report_items': report.report_items}), reports))
            return Response(status=status.HTTP_200_OK, data=ReportDetailSerializer(response, many=True).data)
        except Exception as e:
            logger.error('Error processing request %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST)


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


class ReportsViewSet(viewsets.ViewSet):
    queryset = models.Report.objects.all()
    permission_classes = (IsAuthenticated,)

    def parse_query_params(self, query_params):
        if not query_params:
            return None, None, None, None
        sort = query_params.get('sort', None)
        # if sort:
        #     if getattr(self.model, sort, None):
        #         sort_field = sort
        #     else:
        #         sort_field = 'last_name'
        # else:
        #     sort_field = 'last_name'
        sort_field = ''
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        user_id = query_params.get('userID', None)
        if size:
            try:
                size = int(size)
            except Exception as e:
                size = None
        return query, sort_field, size, user_id

    def get_results(self, query, sort_field, size):
        if query:
            queryset = models.Report.objects.filter(Q(first_name__istartswith=query) | Q(last_name__istartswith=query))
        else:
            queryset = models.Report.objects.all()
        if sort_field:
            queryset = queryset.order_by(sort_field)
        if size:
            queryset = queryset[:int(size)]
        return queryset

    def retrieve(self, request, pk=None):
        # Check if user is admin of this org
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
            if user_org.exists():
                report_items = models.ReportItem.objects.filter(report__uuid=pk)
                serializer = ReportDetailsForWebSerializer(report_items, many=True)
                logger.debug(str(serializer.data))
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def list(self, request):
        try:
            user = request.user
            try:
                user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
                if user_org.exists():
                    query_params = request.query_params
                    query, sort_field, size, user_id = self.parse_query_params(query_params)
                    # physicians = self.get_results(query, sort_field, size)
                    if not user_id:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})

                    reports = models.Report.objects.filter(user__uuid=user_id).order_by('-created_at')
                    reports_serializer = ReportSerializer(reports, many=True)

                    return Response(reports_serializer.data)
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
            except Exception as e:
                logger.error(str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


# Todo: Used for online patients feature in the app
class GetPatientsByOrg(APIView):
    queryset = models.OrganizationPatientsMapping.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = PatientsForOrgSerializer

    def get(self, request):
        user = request.user.profile
        try:
            try:
                user_org = UserOrganizationAccess.objects.get(user=user)
            except Exception as e:
                logger.error('User part of no org or multiple orgs: %s' % str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.NO_OR_MULTIPLE_ORGS_FOR_USER})
            mappings = models.OrganizationPatientsMapping.objects.filter(organization=user_org.organization).select_related('patient', 'patient__address')
            serializer = self.serializer_class(mappings, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error('Cannot fetch patients for org for this user: %s. Error: %s' % (str(user), str(e)))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


# Todo: Used for online patients feature in the app
class AssignPatientToUser(APIView):
    permission_classes = (IsAuthenticated,)

    local_counter = 1

    def post(self, request):
        """
        - find org of calling user
        - check if org has access to patientID passed
        - get active episode for that patientID
        - check if user doesn't already have access to this episode
        - link episode to user
        """
        patient_id = request.data.get('patientID', None)
        if not patient_id:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        try:
            user = request.user.profile

            try:
                # Find this user's organization
                # This assumes user can only belong to 1 org
                user_org = UserOrganizationAccess.objects.get(user=user).organization
            except Exception as e:
                logger.error('User associated with no or multiple Orgs: %s' % str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.NO_OR_MULTIPLE_ORGS_FOR_USER})

            # Throw error if patient doesn't belong to this org
            mapping = models.OrganizationPatientsMapping.objects.filter(organization=user_org).filter(patient_id=patient_id)
            if not mapping.exists():
                logger.error(errors.INVALID_PATIENT_PASSED)
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.INVALID_PATIENT_PASSED})

            try:
                episode = models.Episode.objects.filter(patient_id=patient_id).get(is_active=True)
            except Exception as e:
                logger.error('Missing or Extra active episode for a patientIDs passed')
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

            org_id = user_org.uuid
            user_id = user.uuid

            # Throw error if user already has access to any of the episodes
            access = models.UserEpisodeAccess.objects.filter(user_id=user_id, organization_id=org_id).filter(episode=episode)
            if access.exists():
                logger.error('User already has access to the episode. Cannot add another entry')
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.PATIENT_ALREADY_ASSIGNED})

            # Update the DB
            logger.debug('Saving UserEpisodeAccess Serializer')
            try:
                # Check if entry exists in deleted objects
                deleted_access = models.UserEpisodeAccess.all_objects.exclude(deleted_at=None).get(user_id=user_id, organization_id=org_id, episode=episode)
                deleted_access.deleted_at = None
                deleted_access.save()
            except Exception as e:
                logger.info('No UserEpisodeAccess entry found in deleted objects')
                data = {'organization_id': org_id, 'user_id': user_id, 'episode_id': episode.uuid, 'user_role': 'CareGiver'}
                access_serializer = UserEpisodeAccessSerializer(data=data)
                access_serializer.is_valid()
                access_serializer.save()
            logger.debug('UserEpisodeAccess saved successfully')

            settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                'actionType': 'ASSIGN',
                'patientID': str(patient_id),
                'pn_apns': {
                    "aps": {
                        "content-available": 1
                    },
                    "payload": {
                        "messageCounter": AssignPatientToUser.local_counter,
                        "patientID": str(patient_id)
                    }
                }
            }).async(my_publish_callback)

            settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                'pn_apns': {
                    "aps": {
                        "alert": {
                            "body": "You have a new Patient",
                        },
                        "sound": "default",
                    },
                    "payload": {
                        "messageCounter": AssignPatientToUser.local_counter,
                        "patientID": str(patient_id),
                        "navigateTo": 'patient_list'
                    }
                },
                'pn_gcm': {
                    'data': {
                        'notificationBody': "You have a new Patient",
                        "sound": "default",
                        "navigateTo": 'patient_list',
                        'messageCounter': AssignPatientToUser.local_counter,
                        'patientID': str(patient_id)
                    }
                }
            }).async(my_publish_callback)

            AssignPatientToUser.local_counter += 1
            return Response({'success': True, 'error': None})

        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


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


class AssignedPatientsHistoryDetailView(APIView):
    queryset = models.Patient.objects.all()
    serializer_class = AssignedPatientsHistorySerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        accesses = models.UserEpisodeAccess.all_objects.select_related('episode__patient__address').filter(user=request.user.profile)
        patients = [access.episode.patient for access in accesses]
        active_patient_ids = [str(access.episode.patient.uuid) for access in accesses if not bool(access.deleted_at)]
        response = self.serializer_class(patients, context={'active_ids': active_patient_ids}, many=True)
        return Response(response.data)


class PlacesHistoryDetailView(APIView):
    queryset = models.Place.objects.all()
    serializer_class = PlaceHistoryResponseSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            access = UserOrganizationAccess.objects.select_related('organization').get(user=request.user.profile)
            places = models.Place.all_objects.select_related('address').filter(organization=access.organization)
            return Response(status=status.HTTP_200_OK, data=self.serializer_class(places, many=True).data)
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
