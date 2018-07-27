import dateutil.parser
from django.shortcuts import render
from django.http import Http404
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from rest_framework import generics
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

from backend import errors
from phi import models
from phi.constants import query_to_db_field_map
from phi.serializers import OrganizationPatientMappingSerializer, \
    EpisodeSerializer, PatientPlainObjectSerializer, UserEpisodeAccessSerializer, \
    PatientWithUsersSerializer, PatientUpdateSerializer, \
    PhysicianObjectSerializer, VisitSerializer, PatientWithUsersAndPhysiciansSerializer
from phi.response_serializers import PatientListSerializer, PatientDetailsResponseSerializer, \
    EpisodeDetailsResponseSerializer, VisitDetailsResponseSerializer, PhysicianResponseSerializer, \
    VisitResponseSerializer, PatientDetailsWithOldIdsResponseSerializer
from user_auth.models import UserOrganizationAccess
from user_auth.serializers import AddressSerializer
import logging
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

    def parse_data(self, data):
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
                # TODO: This IS BAAAAD. Change this ASAP to bulk API.
                for userid in users:
                    u = UserOrganizationAccess.objects.filter(organization=organization).filter(user_id=userid)
                    if not u.exists():
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
                            except Exception as e:
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

                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'actionType': 'ASSIGN',
                                    'patientID': str(patient.uuid),
                                    'pn_apns': {
                                        "aps": {
                                            "alert": {
                                                "body": "You have a new Patient",
                                            },
                                            "sound": "default",
                                            "content-available": 1
                                        },
                                        "payload": {
                                            "messageCounter": AccessiblePatientViewSet.local_counter,
                                            "patientID": str(patient.uuid)
                                        }
                                    }
                                }).async(my_publish_callback)

                        user_access_to_delete = models.UserEpisodeAccess.objects.filter(
                            organization=organization).filter(episode_id=episode_id).exclude(user_id__in=users)
                        logger.debug('to delete: %s' % str(user_access_to_delete))

                        for user_episode_access in user_access_to_delete.iterator():
                            logger.debug('user access to delete: %s' % str(user_episode_access))
                            settings.PUBNUB.publish().channel(str(user_episode_access.user_id) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': str(patient.uuid),
                            }).async(my_publish_callback)

                        AccessiblePatientViewSet.local_counter += 1

                        user_access_to_delete.delete()
                    return Response({'success': True})

            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def destroy(self, request, pk=None):
        """
        Delete the details of this patient, if user has access to it.
        :param request:
        :param pk:
        :return:
        """
        # Check if user is admin of this org

        # TODO:
        # Delete org patient mapping
        # delete UserEpisodeAccess for this org
        # Check if patient is mapped to some other org
        # If Yes, delete these episodes
        # If No, delete episodes, patients, addresses

        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
            organization = user_org.organization
            if user_org:
                patient = models.Patient.objects.get(uuid=pk)
                episode_ids = patient.episodes.values_list('uuid', flat=True)      # Choose is_active

                # Org has access to patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization=organization).filter(patient=patient)
                if org_has_access.exists():
                    with transaction.atomic():
                        # models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).filter(patient_id=patient.id).delete()
                        # models.UserEpisodeAccess.objects.filter(organization_id=organization.id).filter(episode_id__in=episode_ids).delete()
                        # q = models.OrganizationPatientsMapping.objects.filter(patient_id=patient.id)
                        # if len(q) == 0:

                        user_episode_accesses = models.UserEpisodeAccess.objects.filter(organization=organization).filter(
                            episode_id__in=episode_ids)

                        for user_episode_access in user_episode_accesses:
                            settings.PUBNUB.publish().channel(
                                str(user_episode_access.user.uuid) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': str(patient.uuid),
                            }).async(my_publish_callback)

                        address = patient.address
                        patient.delete()    # this will also delete the episodes
                        address.delete()
                    logger.info('Delete successful')
                    # else:
                    #     # TODO: IMP: Complete this before pushing to production
                    #     return Response(status=500, data={'success': False, 'error': 'Server Error'})
                    return Response({'success': True, 'error': None})
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
            sort_field = 'first_name'
            order = 'ASC'
            if 'sort' in query_params:
                sort_field = query_to_db_field_map.get(query_params['sort'], sort_field)
                if 'order' in query_params:
                    order = query_params['order']
            if order == 'DESC':
                sort_field = '-' + sort_field

            # Check if this user is admin of the org
            # Note: (A user can be admin of only 1 org)
            try:
                user_org = UserOrganizationAccess.objects.filter(user=user.profile).get(is_admin=True)
                if user_org :
                    logger.debug('User is admin: %s' % str(user))
                    patient_ids = models.OrganizationPatientsMapping.objects.filter(organization=user_org.organization).values_list('patient_id')
                    patients = models.Patient.objects.filter(uuid__in=patient_ids).order_by(sort_field)
                    patient_list = list()
                    # Todo: Extremely SLow Query
                    for patient in patients:
                        episode_ids = patient.episodes.values_list('uuid', flat=True)
                        # print('episode_ids:', episode_ids)
                        user_profile_ids = models.UserEpisodeAccess.objects.filter(episode_id__in=episode_ids).filter(organization=user_org.organization).values_list('user_id', flat=True)
                        patient_list.append({'patient': patient, 'userIds': list(user_profile_ids)})
                    serializer = PatientWithUsersSerializer(patient_list, many=True)
                    return Response(serializer.data)
            except Exception as e:
                logger.error('User is not admin: %s' % str(e))
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
        patient, address, users, physicianId = self.parse_data(data)
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
                                "alert": {
                                    "body": "You have a new Patient",
                                },
                                "sound": "default",
                                "content-available": 1
                            },
                            "payload": {
                                "messageCounter": AccessiblePatientViewSet.local_counter,
                                "patientID": str(patient_obj.uuid)
                            }
                        }
                    }).async(my_publish_callback)

                return Response({'success': True, 'error': None})

        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


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
                    episode = models.Patient.objects.get(id=patient_id).episodes.get(is_active=True)
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
    queryset = models.Physician.objects.all()
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        try:
            user = request.user
            try:
                user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
                if user_org.exists():
                    logger.debug('User is admin')
                    # Todo: Add notion of Physicians being associated to Orgs
                    physicians = models.Physician.objects.all()
                    serializer = PhysicianResponseSerializer(physicians, many=True)
                    logger.debug(str(serializer.data))
                    return Response(serializer.data)
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
            except Exception as e:
                logger.error(str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def create(self, request):
        user_org = UserOrganizationAccess.objects.filter(user=request.user.profile).filter(is_admin=True)
        if user_org.exists():
            physician = request.data.get('physician', None)
            if not physician:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
            try:
                physician_serializer = PhysicianObjectSerializer(data=physician)
                if physician_serializer.is_valid():
                    physician_serializer.save()
                    return Response({'success': True, 'error': None})
                else:
                    logger.error('Error in creating physician: %s' % str(physician_serializer.errors))
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
            except Exception as e:
                logger.error(str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})

    def retrieve(self, request, pk=None):
        # Check if user is admin of this org
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
            if user_org.exists():
                # Todo: Add notion of Physicians being associated to Orgs; Do permission checks
                physician = models.Physician.objects.get(uuid=pk)
                serializer = PhysicianResponseSerializer(physician)
                logger.debug(str(serializer.data))
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


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
            visits = models.Visit.objects.filter(user=user)
            serializer = self.serializer_class(visits, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error('Error in fetching visits for this user: %s' % str(user))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


class GetVisitsView(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = VisitDetailsResponseSerializer

    def get_results(self, request):
        data = request.data
        if 'visitIDs' in data:
            visit_ids = data['visitIDs']

            success = list()
            failure_ids = list()
            for visit_id in visit_ids:
                try:
                    # Allow users to query all visits from the same Org
                    orgs = UserOrganizationAccess.objects.filter(user=request.user.profile).values_list('organization', flat=True)
                    visit = models.Visit.objects.filter(organization__in=orgs).get(pk=visit_id)
                    success.append(visit)
                except Exception as e:
                    logger.error('Visit not found: %s' % (str(e)))
                    failure_ids.append(visit_id)
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

    def post(self, request):
        # Check user permissions for that episode
        visits = request.data.get('visits')
        if not visits:
            logger.error('"visits" not present in request')
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})

        success = list()
        failure = list()

        # Check permission for, validate and save each visit
        for visit in visits:
            episode_id = visit.get('episodeID')
            if not episode_id:
                logger.warning('Not saving. EpisodeID not received for visit: %s' % str(visit))
                failure.append(visit)
                continue
            # Todo: Handle case of same-user-multiple-orgs
            try:
                org = models.UserEpisodeAccess.objects.filter(user=request.user.profile).get(episode_id=episode_id).organization
            except Exception as e:
                logger.warning('Not saving visit. Error: %s' % str(e))
                failure.append(visit)
                continue

            serializer = VisitSerializer(data=visit)
            if serializer.is_valid():
                try:
                    serializer.save(user=request.user.profile, organization=org)
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
            org = models.UserEpisodeAccess.objects.filter(user=request.user.profile).get(episode_id=visit.episode_id).organization
        except Exception as e:
            logger.error('Not saving visit. Error: %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.VISIT_NOT_EXIST})

        serializer = VisitSerializer(instance=visit, data=request.data)
        if not serializer.is_valid():
            logger.error(str(serializer.errors))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        try:
            serializer.save(user=request.user.profile, organization=org)
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
        success_ids = list()
        failure_ids = list()
        if 'visitIDs' in data:
            visit_ids = data['visitIDs']
            for visit_id in visit_ids:
                try:
                    visit = models.Visit.objects.filter(user=user.profile).get(pk=visit_id)
                    visit.delete()
                    success_ids.append(visit_id)
                except Exception as e:
                    logger.error('Visit not found or cannot delete: %s' % (str(e)))
                    failure_ids.append(visit_id)
            return success_ids, failure_ids
        return None, None

    def delete(self, request):
        success_ids, failure_ids = self.get_results(request)
        if (not success_ids) and (not failure_ids):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        return Response({'success': success_ids, 'failure': failure_ids})
