from rest_framework import viewsets
from phi import models
from phi.serializers import PatientSerializer

# Create your views here.


class PatientViewSet(viewsets.ModelViewSet):
    queryset = models.Patient.objects.all()
    serializer_class = PatientSerializer

    def get_queryset(self):
        user = self.request.user

        # Todo: Move to a middleware/decorator ???
        # Access Control Resolution
        # Todo: Fetch User Episode Access, Also, return org in result
        objects = models.UserEpisodeAccess.objects.filter(user__id=user.profile.id)
        print('Length of objects:')
        print(len(objects))
        patients = list()
        for obj in objects:
            patients.append(obj.episode.patient)
        # Todo: Return ids of episodes this user has access to
        return patients
