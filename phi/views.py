from rest_framework import viewsets
from phi import models
from user_auth.models import UserOrganizationAccess
from phi.serializers import PatientSerializer, PatientListSerializer, \
    PatientDetailsResponseSerializer, OrganizationPatientMappingSerializer, \
    EpisodeSerializer, PatientPlainObjectSerializer, UserEpisodeAccessSerializer
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
    """
    Currently writing for add operations
    """
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

    def create(self, request, format=None):
        """
        Within Single Transaction:
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

                # Find this user's organization and Check if this user is the admin
                # Only admin should have write permissions
                user_org = UserOrganizationAccess.objects.filter(user__id=user.profile.id).get(is_admin=True)
                organization = user_org.organization

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
            return Response({'success': False, 'error': str(e)})


# Being Used for app API
class AccessiblePatientListView(generics.ListAPIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # todo: fix this before Prod
        objects = models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).select_related('episode__patient').values_list('id', flat=True) # noqa
        return objects

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PatientListSerializer({'patients': list(queryset)})
        return Response(serializer.data)


# Being used for app API
# Todo: Errors have been hardcoded
class AccessiblePatientsDetailView(APIView):
    # Todo: Add permissions classes + check for access etc
    queryset = models.Patient.objects.all()
    serializer_class = PatientDetailsResponseSerializer
    permission_classes = (IsAuthenticated,)

    # Todo: Check if user has access to those ids first
    def get_queryset(self, request):
        data = request.data
        if 'patients' in data:
            patient_list = data['patients']
            return models.Patient.objects.all().filter(id__in=patient_list)
        return None

    def post(self, request):
        queryset = self.get_queryset(request)
        # Todo: Handle errors here;
        resp = {'success': queryset, 'failure': [{'id': 10000, 'error': 'Some error'}]}
        serializer = PatientDetailsResponseSerializer(resp)
        return Response(serializer.data)
