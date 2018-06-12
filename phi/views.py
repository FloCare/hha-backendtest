from rest_framework import viewsets
from phi import models
from phi.serializers import PatientSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.


class AllPatientsViewset(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer
    # Todo: Enable in production ?
    # permission_classes = (IsAuthenticated,)


class AccessiblePatientViewSet(viewsets.ModelViewSet):
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
        # Todo: Return ids of episodes this user has access to
        return patients

