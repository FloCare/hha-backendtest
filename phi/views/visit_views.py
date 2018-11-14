from backend import errors
from django.db import IntegrityError
from phi import models
from phi.data_services.visit_data_service import VisitDataService
from phi.exceptions.InvalidDataForSerializerException import InvalidDataForSerializerException
from phi.migration_helpers import MigrationHelpers
from phi.serializers.response_serializers import VisitDetailsResponseSerializer, VisitResponseSerializer, \
    VisitForOrgResponseSerializer
from phi.serializers.serializers import OrganizationPatientMappingSerializer, EpisodeSerializer, VisitSerializer, \
    VisitMilesSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth.models import UserOrganizationAccess, Address

import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


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
            logger.error('Error in fetching visits for this user: %s' % str(user))
            logger.error(e)
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
            MigrationHelpers.handle_miles_migration(visit_miles)
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
            UserOrganizationAccess.objects.get(user=request.user.profile).organization
        except UserOrganizationAccess.DoesNotExist as e:
            logger.error('Not saving visit. Error: %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': 'User has no organisation'})

        try:
            DataServices.visit_data_service().update_visit(request.user.profile, visit, request.data)
        except InvalidDataForSerializerException as e:
            logger.error('Invalid data for serializer exception, %s ' % str(e))
            logger.error(traceback.format_exc(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        except IntegrityError as e:
            logger.error('IntegrityError. Cannot update visit: %s' % str(e))
            logger.error(traceback.format_exc(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.DATA_INVALID})
        except Exception as e:
            logger.error('Cannot update visit: %s' % str(e))
            logger.error(traceback.format_exc(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        return Response({'success': True, 'error': None})


class BulkUpdateVisitView(APIView):
    queryset = models.Visit.objects.all()
    permission_classes = (IsAuthenticated,)

    def update_single_visit(self, user_profile, visit_id, data):
        try:
            visit = models.Visit.objects.get(pk=visit_id)
            DataServices.visit_data_service().update_visit(user_profile, visit, data)
        except models.Visit.DoesNotExist:
            logger.error('Visit with id : %s does not exist' % str(visit_id))

    def post(self, request):
        data = request.data
        counter = 0
        visits = data.get('visits', [])
        for visit in visits:
            try:
                self.update_single_visit(request.user.profile, visit['visitID'], visit)
                counter += 1
            except InvalidDataForSerializerException as e:
                logger.error('Invalid data for serializer exception, %s ' % str(e))
                logger.error(traceback.format_exc(e))
            except IntegrityError as e:
                logger.error('IntegrityError. Cannot update visit: %s' % str(e))
                logger.error(traceback.format_exc(e))
        return Response(status=status.HTTP_200_OK, data={'success': True, 'count': counter})


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


class DataServices:
    @staticmethod
    def visit_data_service():
        return VisitDataService()
