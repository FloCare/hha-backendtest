from backend import errors
from django.conf import settings
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import render
from phi import models
from phi.forms import UploadFileForm
from phi.response_serializers import AssignedPatientsHistorySerializer, PlaceHistoryResponseSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth.models import UserOrganizationAccess

import logging

logger = logging.getLogger(__name__)


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


class PatientsForSyncView(APIView):
    queryset = models.Patient.objects.all()
    serializer_class = AssignedPatientsHistorySerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        accesses = models.UserEpisodeAccess.all_objects.select_related('episode__patient__address').filter(user=request.user.profile)
        patients = [access.episode.patient for access in accesses]
        active_patient_ids = [str(access.episode.patient.uuid) for access in accesses if not bool(access.deleted_at)]
        response = self.serializer_class(patients, context={'active_ids': active_patient_ids}, many=True)
        return Response(response.data)


class PlacesForSyncView(APIView):
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
