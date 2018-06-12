from rest_framework import viewsets
from phi import models
from phi.serializers import PatientSerializer, PatientListSerializer
from rest_framework import generics
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AllPatientsViewset(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    # Todo: Enable in production ?
    # permission_classes = (IsAuthenticated,)


class AccessiblePatientViewSet(viewsets.ModelViewSet):
    # TODO: Which model to query on?
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    # Todo: Enable in production ?
    # permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user

        # Access Control Resolution
        # Todo: Move access control to a middleware/decorator ???

        # Todo: Fetch User Episode Access, Also, return org in result
        objects = models.UserEpisodeAccess.objects.all()    # filter(user__id=user.profile.id)
        patients = list()
        for obj in objects:
            patients.append(obj.episode.patient)
        return patients


class AccessiblePatientListView(generics.ListAPIView):
    queryset = models.Patient.objects.all()
    serializer_class = PatientListSerializer
    # permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        #user = self.request.user
        # todo: fix this before Prod
        objects = models.UserEpisodeAccess.objects.all().select_related('episode__patient') # filter(user__id=user.profile.id).
        return objects

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PatientListSerializer(queryset, many=True)
        return Response(serializer.data)
