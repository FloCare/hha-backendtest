from backend import errors
from django.db import transaction
from django.db.models import Q
from phi import models
from phi.constants import total_miles_buffer_allowed
from phi.exceptions.TotalMilesDidNotMatchException import TotalMilesDidNotMatchException
from phi.exceptions.VisitsNotFoundException import VisitsNotFoundException
from phi.serializers.response_serializers import ReportSerializer, ReportDetailSerializer, ReportDetailsForWebSerializer
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user_auth.models import UserOrganizationAccess

import logging
import uuid

logger = logging.getLogger(__name__)


class ReportsViewSet(viewsets.ViewSet):
    queryset = models.Report.objects.all()
    permission_classes = (IsAuthenticated,)

    def parse_query_params(self, query_params):
        if not query_params:
            return None, None, None, None
        sort = query_params.get('sort', None)
        # if sort:
        #     if getattr(self.model, sort, None):
        #         sort_field = sort
        #     else:
        #         sort_field = 'last_name'
        # else:
        #     sort_field = 'last_name'
        sort_field = ''
        query = query_params.get('query', None)
        size = query_params.get('size', None)
        user_id = query_params.get('userID', None)
        if size:
            try:
                size = int(size)
            except Exception as e:
                size = None
        return query, sort_field, size, user_id

    def get_results(self, query, sort_field, size):
        if query:
            queryset = models.Report.objects.filter(Q(first_name__istartswith=query) | Q(last_name__istartswith=query))
        else:
            queryset = models.Report.objects.all()
        if sort_field:
            queryset = queryset.order_by(sort_field)
        if size:
            queryset = queryset[:int(size)]
        return queryset

    def retrieve(self, request, pk=None):
        # Check if user is admin of this org
        try:
            user = request.user
            user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
            if user_org.exists():
                report_items = models.ReportItem.objects.filter(report__uuid=pk)
                serializer = ReportDetailsForWebSerializer(report_items, many=True)
                logger.debug(str(serializer.data))
                return Response(serializer.data)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})

    def list(self, request):
        try:
            user = request.user
            try:
                user_org = UserOrganizationAccess.objects.filter(user=user.profile).filter(is_admin=True)
                if user_org.exists():
                    query_params = request.query_params
                    query, sort_field, size, user_id = self.parse_query_params(query_params)
                    # physicians = self.get_results(query, sort_field, size)
                    if not user_id:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.USER_NOT_EXIST})

                    reports = models.Report.objects.filter(user__uuid=user_id).order_by('-created_at')
                    reports_serializer = ReportSerializer(reports, many=True)

                    return Response(reports_serializer.data)
                else:
                    return Response(status=status.HTTP_401_UNAUTHORIZED, data={'success': False, 'error': errors.ACCESS_DENIED})
            except Exception as e:
                logger.error(str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})
        except Exception as e:
            logger.error(str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'success': False, 'error': errors.UNKNOWN_ERROR})


class CreateReportForVisits(APIView):
    permission_classes = (IsAuthenticated,)

    def get_report_item_object(self, report, report_item, visits_map):
        visit = visits_map[uuid.UUID(report_item['visitID'])]
        return models.ReportItem(uuid=report_item['reportItemId'], report=report, visit=visit)

    def post(self, request):
        user = request.user
        data = request.data
        report_items = data['reportItems']
        report_id = data['reportID']
        logger.info('Payload for create report : %s' % str(data))
        total_miles_in_app_report = data['totalMiles']
        try:
            existing_report = models.Report.objects.get(uuid=report_id)
            existing_report_items = existing_report.report_items
            report_item_ids_in_db = list(existing_report_items.values_list("uuid", flat=True))
            report_item_ids = list(map((lambda item: uuid.UUID(item['reportItemId'])), report_items))
            if set(report_item_ids_in_db) == set(report_item_ids):
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_409_CONFLICT)
        except models.Report.DoesNotExist:
            response_data = {}
            try:
                with transaction.atomic():
                    report = models.Report(uuid=report_id, user=user.profile)
                    report.save()
                    visit_ids = list(map(lambda item : uuid.UUID(item['visitID']), report_items))
                    visits = models.Visit.all_objects.select_related('visit_miles').in_bulk(visit_ids, field_name="id")
                    visit_ids_in_db = visits.keys()
                    missing_visit_ids = list(set(visit_ids) - set(visit_ids_in_db))
                    if len(missing_visit_ids) > 0:
                        response_data = {'missingVisitIDs': missing_visit_ids}
                        raise VisitsNotFoundException(missing_visit_ids)
                    total_miles_travelled = 0
                    for visit_id in visits:
                        visit_miles = visits[visit_id].visit_miles
                        if visit_miles and visit_miles.computed_miles is not None:
                            total_miles_travelled += visit_miles.computed_miles
                            if visit_miles.extra_miles is not None:
                                total_miles_travelled += visit_miles.extra_miles
                    difference_in_db_and_app = abs(total_miles_travelled - total_miles_in_app_report)
                    if difference_in_db_and_app > total_miles_buffer_allowed:
                        raise TotalMilesDidNotMatchException(total_miles_in_app_report, total_miles_travelled)
                    report_items = [self.get_report_item_object(report, report_item, visits) for report_item in report_items]
                    models.ReportItem.objects.bulk_create(report_items)
                return Response(status=status.HTTP_201_CREATED)
            except VisitsNotFoundException as e:
                logger.error('Visits Not Found Exception raised : %s', str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)
            except TotalMilesDidNotMatchException as e:
                logger.error('Total Miles Did not match exception raised %s', str(e))
                return Response(status=status.HTTP_400_BAD_REQUEST, data=response_data)


class GetReportsForUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        reports = models.Report.objects.filter(user=request.user.profile)
        reports_serializer = ReportSerializer(reports, many=True)
        return Response(status=status.HTTP_200_OK, data=reports_serializer.data)


class GetReportsDetailByIDs(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data
        report_ids = data['reportIDs']
        try:
            reports = models.Report.objects.prefetch_related("report_items__visit").in_bulk(report_ids, field_name='uuid').values()
            response = list(map((lambda report : {'report': report, 'report_items': report.report_items}), reports))
            return Response(status=status.HTTP_200_OK, data=ReportDetailSerializer(response, many=True).data)
        except Exception as e:
            logger.error('Error processing request %s' % str(e))
            return Response(status=status.HTTP_400_BAD_REQUEST)

