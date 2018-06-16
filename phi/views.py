from rest_framework import viewsets
from phi import models
from user_auth.models import UserOrganizationAccess, UserProfile
from phi.serializers import PatientSerializerWeb, PatientListSerializer, \
    PatientDetailsResponseSerializer, OrganizationPatientMappingSerializer, \
    EpisodeSerializer, PatientPlainObjectSerializer, UserEpisodeAccessSerializer, \
    PatientWithUsersSerializer
from user_auth.serializers import AddressSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

# Create your views here.


# class AllPatientsViewset(viewsets.ModelViewSet):
#     queryset = models.Patient.objects.all()
#     serializer_class = PatientSerializer
#     # permission_classes = (IsAuthenticated,)


# # Todo: Add org to response; episode ???
# class AccessiblePatientsViewSet(viewsets.ModelViewSet):
#     queryset = models.Patient.objects.all()
#     serializer_class = PatientSerializer
#     # Todo: Enable in production
#     permission_classes = (IsAuthenticated,)
#
#     def get_queryset(self):
#         user = self.request.user
#
#         # Access Control Resolution
#         # Todo: Move access control to a middleware/decorator
#
#         # Todo: Fetch User Episode Access, Also, return org in result
#         objects = models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).select_related('episode__patient')
#         patients = list()
#         for obj in objects:
#             patients.append(obj.episode.patient)
#         return patients


class AccessiblePatientViewSet(viewsets.ViewSet):
    queryset = models.Patient.objects.all()
    permission_classes = (IsAuthenticated,)

    def parse_data(self, data):
        try:
            patient = data['patient']
            address = patient.pop('address')
            # address = patient['address']
            users = data['users']
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
                return Response({'error': 'Invalid data passed'})
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
                        # Todo: Do not delete admin's accesses
                        models.UserEpisodeAccess.objects.filter(organization_id=organization.id).delete()

                        for user_id in users:
                            access_serializer = UserEpisodeAccessSerializer(data={'organization_id': organization.id,
                                                                                  'user_id': user_id,
                                                                                  'episode_id': episode_id,
                                                                                  'user_role': 'CareGiver'})
                            access_serializer.is_valid()
                            access_serializer.save()
                    return Response({'success': True})

            return Response(status=401, data={'success': False, 'error': 'Access denied'})
        except Exception as e:
            print('Error:', str(e))
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

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
            if user_org :
                patient = models.Patient.objects.get(id=pk)
                episode_ids = patient.episodes.values_list('id', flat=True)      # Choose is_active

                # Org has access to patient
                org_has_access = models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).get(patient_id=patient.id)
                if org_has_access:

                    with transaction.atomic():
                        models.OrganizationPatientsMapping.objects.filter(organization_id=organization.id).filter(patient_id=patient.id).delete()
                        models.UserEpisodeAccess.objects.filter(organization_id=organization.id).delete()
                        q = models.OrganizationPatientsMapping.objects.filter(patient_id=patient.id)
                        if len(q) == 0:
                            address = patient.address
                            address.delete()
                            patient.delete()    # this will also delete the episodes
                            print('Delete successful')
                        else:
                            # pass
                            # TODO: IMP: Complete this before pushing to production
                            return Response(status=500, data={'success': False, 'error': 'Server Error'})
                    return Response({'success': True, 'error': None})
            return Response(status=401, data={'success': False, 'error': 'Access denied'})
        except Exception as e:
            print('Error:', str(e))
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

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
                    user_profile_ids = models.UserEpisodeAccess.objects.filter(episode_id__in=episode_ids).filter(organization_id=organization.id).values_list('user_id')
                    print('users registered for this patient:', user_profile_ids)
                    users = UserProfile.objects.filter(id__in=user_profile_ids)
                    serializer = PatientWithUsersSerializer({'id': patient.id, 'patient': patient, 'users': users})
                    return Response(serializer.data)
            return Response(status=401, data={'success': False, 'error': 'Access denied'})
        except Exception as e:
            print('Error:', str(e))
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

    def list(self, request):
        """
        Return list of details of patients this user has access to.
        :param request:
        :return:
        """
        try:
            user = request.user
            # Check if this user is admin of the org
            # Note: (A user can be admin of only 1 org)
            try:
                user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
                if user_org :
                    print('User is admin')
                    patient_ids = models.OrganizationPatientsMapping.objects.filter(organization_id=user_org.organization.id).values_list('patient_id')
                    patients = models.Patient.objects.filter(id__in=patient_ids)
                    serializer = PatientSerializerWeb(patients, many=True)
                    return Response(serializer.data)
            except Exception as e:
                print('Error: User is not admin: ', str(e))

            # Check if user has episodes to his name
            # TODO: ALSO CHECK REQUEST USER'S ORGANIZATION
            episode_ids = list(models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).values_list('episode_id', flat=True))  # noqa
            patients = list()
            for episode_id in episode_ids:
                patients.append(models.Episode.objects.get(id=episode_id).patient)
            serializer = PatientSerializerWeb(patients, many=True)
            return Response(serializer.data)
        except Exception as e:
            print('Error:', e)
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})

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
            return Response({'error': 'Invalid data passed'})
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

                return Response({'success': True, 'error': None})

        except Exception as e:
            print(e)
            return Response(status=400, data={'success': False, 'error': 'Something went wrong'})


# Being Used for app API
class AccessiblePatientListView(generics.ListAPIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # todo: fix this before Prod
        episode_ids = list(models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).values_list('episode_id', flat=True)) # noqa
        patient_ids = list()
        for episode_id in episode_ids:
            patient_ids.append(models.Episode.objects.get(id=episode_id).patient.id)
        return patient_ids

    def list(self, request):
        patient_list = self.get_queryset()
        serializer = PatientListSerializer({'patients': patient_list})
        return Response(serializer.data)


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
            failure.append({'id': id, 'error': 'Access denied'})
        resp = {'success': success, 'failure': failure}
        serializer = PatientDetailsResponseSerializer(resp)
        return Response(serializer.data)
