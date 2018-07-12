from django.db import transaction
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
from phi.serializers import PatientListSerializer, \
    PatientDetailsResponseSerializer, OrganizationPatientMappingSerializer, \
    EpisodeSerializer, PatientPlainObjectSerializer, UserEpisodeAccessSerializer, \
    PatientWithUsersSerializer, PatientUpdateSerializer, \
    PhysicianObjectSerializer, PhysicianResponseSerializer
from user_auth.models import UserOrganizationAccess
from user_auth.serializers import AddressSerializer


def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        print("# Message successfully published to specified channel.")
    else:
        print("# NOT Message successfully published to specified channel.")
        pass  # Handle message publish error. Check 'category' property to find out possible issue
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
            #physicianId = data['physicianId']
            # address = patient['address']
            if 'users' in data:
                users = data['users']
            else:
                users = []
            return patient, address, users
        except Exception as e:
            print('Incorrect or Incomplete data passed:', e)
            return None, None, None

    def update(self, request, pk=None):
        """
        Update the users associated to this patient
        :param request:
        :param pk:
        :return:
        """
        try:
            user = request.user
            data = request.data
            if 'users' not in data:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': 'Invalid data passed'})
            users = data['users']

            # Check if caller is an admin
            user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            organization = user_org.organization
            if user_org :

                # Check if the passed users belong to this organization
                # Someone might maliciously pass invalid users
                # TODO: This IS BAAAAD. Change this ASAP to bulk API.
                for userid in users:
                    u = UserOrganizationAccess.objects.filter(organization__id=organization.id).get(user__id=userid)
                    if not u:
                        raise Exception('Invalid user passed')

                patient = models.Patient.objects.get(id=pk)
                episode_ids = patient.episodes.values_list('id', flat=True)      # Choose is_active

                # Todo: Remove this hack
                # Get the last Episode ID
                if len(episode_ids) == 0:
                    raise Exception('No episodes registered for this patient')
                episode_id = list(episode_ids)[-1]
                print('org-id:', organization.id)
                print('patient-id:', patient.id)

                # Check if org has access to this patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).get(patient_id=patient.id)
                if org_has_access:
                    with transaction.atomic():
                        # Update patient fields
                        patient_obj = models.Patient.objects.get(id=data['id'])
                        serializer = PatientUpdateSerializer(patient_obj, data=data['patient'], partial=True)
                        serializer.is_valid()
                        serializer.save()

                        # Add the users sent in the payload
                        for user_id in users:
                            try:
                                models.UserEpisodeAccess.objects \
                                    .get(organization_id=organization.id, episode_id=episode_id, user_id=user_id)
                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'actionType': 'UPDATE',
                                    'patientID': patient.id,
                                }).async(my_publish_callback)
                            except:
                                access_serializer = UserEpisodeAccessSerializer(
                                    data={'organization_id': organization.id,
                                          'user_id': user_id,
                                          'episode_id': episode_id,
                                          'user_role': 'CareGiver'})
                                access_serializer.is_valid()
                                access_serializer.save()
                                print('new episode access created for userid:', user_id)

                                settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                                    'actionType': 'ASSIGN',
                                    'patientID': patient.id,
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
                                            "patientID": patient.id
                                        }
                                    }
                                }).async(my_publish_callback)

                        user_access_to_delete = models.UserEpisodeAccess.objects.filter(
                            organization_id=organization.id).filter(episode_id=episode_id).exclude(user_id__in=users)
                        print('to delete:', user_access_to_delete)

                        for user_episode_access in user_access_to_delete.iterator():
                            print('user access to delete:', user_episode_access)
                            settings.PUBNUB.publish().channel(str(user_episode_access.user.id) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': patient.id,
                            }).async(my_publish_callback)

                        AccessiblePatientViewSet.local_counter += 1

                        user_access_to_delete.delete()
                    return Response({'success': True})

            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            print('Error:', str(e))
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
            user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            organization = user_org.organization
            if user_org:
                patient = models.Patient.objects.get(id=pk)
                episode_ids = patient.episodes.values_list('id', flat=True)      # Choose is_active

                # Org has access to patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).get(patient_id=patient.id)
                if org_has_access:
                    with transaction.atomic():
                        # models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).filter(patient_id=patient.id).delete()
                        # models.UserEpisodeAccess.objects.filter(organization_id=organization.id).filter(episode_id__in=episode_ids).delete()
                        # q = models.OrganizationPatientsMapping.objects.filter(patient_id=patient.id)
                        # if len(q) == 0:

                        user_episode_accesses = models.UserEpisodeAccess.objects.filter(organization_id=organization.id).filter(
                            episode_id__in=episode_ids)

                        for user_episode_access in user_episode_accesses:
                            settings.PUBNUB.publish().channel(
                                str(user_episode_access.user.id) + '_assignedPatients').message({
                                'actionType': 'UNASSIGN',
                                'patientID': patient.id,
                            }).async(my_publish_callback)

                        address = patient.address
                        patient.delete()    # this will also delete the episodes
                        address.delete()
                    print('Delete successful')
                    # else:
                    #     # TODO: IMP: Complete this before pushing to production
                    #     return Response(status=500, data={'success': False, 'error': 'Server Error'})
                    return Response({'success': True, 'error': None})
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            print('Error:', str(e))
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
            user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            organization = user_org.organization
            if user_org :
                patient = models.Patient.objects.get(id=pk)
                episode_ids = patient.episodes.values_list('id', flat=True)      # Choose is_active

                # Org has access to patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).get(patient_id=patient.id)
                if org_has_access:
                    user_profile_ids = models.UserEpisodeAccess.objects.filter(episode_id__in=episode_ids).filter(organization_id=organization.id).values_list('user_id', flat=True)
                    # print('users registered for this patient:', list(user_profile_ids))
                    #users = UserProfile.objects.filter(id__in=user_profile_ids)
                    serializer = PatientWithUsersSerializer({'id': patient.id, 'patient': patient, 'userIds': list(user_profile_ids)})
                    return Response(serializer.data)
            return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            print('Error:', str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

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
                user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
                if user_org :
                    print('User is admin')
                    patient_ids = models.OrganizationPatientsMapping.objects.filter(organization_id=user_org.organization.id).values_list('patient_id')
                    patients = models.Patient.objects.filter(id__in=patient_ids).order_by(sort_field)
                    patient_list = list()
                    # Todo: Extremely SLow Query
                    for patient in patients:
                        episode_ids = patient.episodes.values_list('id', flat=True)
                        #print('episode_ids:', episode_ids)
                        user_profile_ids = models.UserEpisodeAccess.objects.filter(episode_id__in=episode_ids).filter(organization_id=user_org.organization.id).values_list('user_id', flat=True)
                        patient_list.append({'patient': patient, 'userIds': list(user_profile_ids)})
                    serializer = PatientWithUsersSerializer(patient_list, many=True)
                    return Response(serializer.data)
            except Exception as e:
                print('Error: User is not admin: ', str(e))
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
            print('Error:', e)
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
        patient, address, users = self.parse_data(data)
        if (not patient) or (not address):
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'error': errors.DATA_INVALID})
        try:
            # Find this user's organization and Check if this user is the admin
            # Only admin should have write permissions
            user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            organization = user_org.organization

            # Check if the passed users belong to this organization
            # Someone might maliciously pass invalid users
            # TODO: This IS BAAAAD. Change this ASAP to bulk API.
            for userid in users:
                u = UserOrganizationAccess.objects.filter(organization__id=organization.id).get(user__id=userid)
                if not u:
                    raise Exception('Invalid user passed')

            with transaction.atomic():
                # Save Address
                serializer = AddressSerializer(data=address)
                serializer.is_valid()
                address_obj = serializer.save()

                # # Save Patient
                patient['address_id'] = address_obj.id
                patient_serializer = PatientPlainObjectSerializer(data=patient)
                patient_serializer.is_valid()
                patient_obj = patient_serializer.save()

                # Save Episode
                episode = {
                    'patient_id': patient_obj.id,
                    'soc_date': patient.get('soc_date') or None,
                    'end_date': patient.get('end_date') or None,
                    'period': patient.get('period') or None,
                    'is_active': True,
                    'cpr_code': patient.get('cpr_code') or None,
                    'transportation_level': patient.get('transportation_level') or None,
                    'acuity_type': patient.get('acuity_type') or None,
                    'classification': None,
                    'allergies': None,
                    'pharmacy': None,
                    'soc_clinician': None,
                    'attending_physician': None,
                    'primary_physician': None
                }
                episode_serializer = EpisodeSerializer(data=episode)
                episode_serializer.is_valid()
                episode_obj = episode_serializer.save()

                # Link Patient to Org
                mapping_serializer = OrganizationPatientMappingSerializer(data={'organization_id': organization.id,
                                                                                'patient_id': patient_obj.id})
                mapping_serializer.is_valid()
                mapping_serializer.save()

                # Link Episode to Users passed
                # Todo: Do a bulk update
                for user_id in users:
                    access_serializer = UserEpisodeAccessSerializer(data={'organization_id': organization.id,
                                                                          'user_id': user_id,
                                                                          'episode_id': episode_obj.id,
                                                                          'user_role': 'CareGiver'})
                    access_serializer.is_valid()
                    access_serializer.save()

                    settings.PUBNUB.publish().channel(str(user_id) + '_assignedPatients').message({
                        'actionType': 'ASSIGN',
                        'patientID': patient_obj.id,
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
                                "patientID": patient_obj.id
                            }
                        }
                    }).async(my_publish_callback)

                return Response({'success': True, 'error': None})

        except Exception as e:
            print(e)
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


# Being Used for app API
class AccessiblePatientListView(generics.ListAPIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Todo: Also pass Organization for filtering
        accesses = models.UserEpisodeAccess.objects.filter(user__id=user.profile.id)
        patient_ids = [access.episode.patient.id for access in accesses]
        return patient_ids

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(data={'patients': queryset})
        serializer.is_valid()
        return Response(serializer.validated_data)


# Being used for app API
# Todo: Errors have been hardcoded
class AccessiblePatientsDetailView(APIView):
    # Todo: Add permissions classes + check for access etc
    queryset = models.Patient.objects.all()
    serializer_class = PatientDetailsResponseSerializer
    permission_classes = (IsAuthenticated,)

    # Todo: Check if user has access to those ids first
    def get_results(self, request):
        user = request.user
        data = request.data
        if 'patients' in data:
            patient_list = data['patients']

            # Todo: Improve Queries
            episode_ids = list(models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).values_list('episode_id', flat=True)) # noqa
            valid_ids = list()
            for episode_id in episode_ids:
                valid_ids.append(models.Episode.objects.get(id=episode_id).patient.id)

            success_ids = list(set(valid_ids).intersection(patient_list))
            failure_ids = list(set(patient_list) - set(success_ids))
            return models.Patient.objects.all().filter(id__in=success_ids), failure_ids
        return None

    def post(self, request):
        success, failure_ids = self.get_results(request)
        print('success:', success)
        failure = list()
        for id in failure_ids:
            failure.append({'id': id, 'error': errors.ACCESS_DENIED})
        resp = {'success': success, 'failure': failure}
        serializer = PatientDetailsResponseSerializer(resp)
        return Response(serializer.data)


# Todo: Revisit these when adding physician capabilities
class PhysiciansViewSet(viewsets.ViewSet):

    queryset = models.Physician.objects.all()
    permission_classes = (IsAuthenticated,)

    def parse_data(self, data):
            try:
                physician = data['physician']
                return physician;
            except Exception as e:
                return None

    def list(self, request):
        try:
            user = request.user
            try:
                user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
                if user_org:
                    print('User is admin')

                    physicians = models.Physician.objects.all()
                    serializer = PhysicianResponseSerializer(physicians, many=True)
                    headers = {'Content-Type': 'application/json'}
                    print(serializer.data)
                    return Response(serializer.data, headers=headers)
            except Exception as e:
                print(e)
                return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

        except Exception as e:
            print('Error:', e)
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

    # Todo: Add admin permission check
    def create(self, request):
        user = request.user
        data = request.data

        physician = self.parse_data(data)
        if (not physician):
            return Response(status=400, data={'error': 'Invalid data passed'})

        try:
            physician_serializer = PhysicianObjectSerializer(data=physician)
            physician_serializer.is_valid()
            physician_obj = physician_serializer.save()

            return Response({'success': True, 'error': None})

        except Exception as e:
            print(e)
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

    def retrieve(self, request, pk=None):
        # Check if user is admin of this org
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
            organization = user_org.organization
            physician = models.Physician.objects.get(id=pk)
            serializer = PhysicianResponseSerializer(physician)
            headers = {'Content-Type': 'application/json'}
            print(serializer.data)
            return Response(serializer.data, headers=headers)
        except Exception as e:
            print('Error:', str(e))
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass