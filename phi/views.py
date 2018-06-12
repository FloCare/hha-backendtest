from rest_framework import viewsets
from phi import models
from phi.serializers import PatientSerializer, PatientListSerializer, PatientDetailsResponseSerializer
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AllPatientsViewset(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    # Todo: Enable in production ?
    # permission_classes = (IsAuthenticated,)


# Todo: Add org to response; episode ???
class AccessiblePatientsViewSet(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    # Todo: Enable in production
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        # Access Control Resolution
        # Todo: Move access control to a middleware/decorator

        # Todo: Fetch User Episode Access, Also, return org in result
        objects = models.UserEpisodeAccess.objects.filter(user__id=user.profile.id).select_related('episode__patient')
        patients = list()
        for obj in objects:
            patients.append(obj.episode.patient)
        return patients



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
