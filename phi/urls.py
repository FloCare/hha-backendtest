from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'patients', views.AccessiblePatientViewSet)                                    # admin
router.register(r'physicians', views.PhysiciansViewSet)                                         # admin
# router.register(r'visits', views.VisitsViewSet)
router.register(r'reports', views.ReportsViewSet)
router.register(r'places', views.PlacesViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^get-assigned-patient-ids/$', views.AccessiblePatientListView.as_view()),             # app
            url(r'^get-patients-for-ids/$', views.AccessiblePatientsDetailView.as_view()),              # app
            # Todo: Temporary EndPoint to support migrating apps from 0.2.0 to Next Version
            url(r'^get-patients-for-old-ids/$', views.GetPatientsByOldIds.as_view()),                   # app
            # Todo: Endpoints for online patients feature in the app
            url(r'^get-patients-for-org/$', views.GetPatientsByOrg.as_view()),                          # app
            url(r'^add-patient-to-user/$', views.AssignPatientToUser.as_view()),                        # app
            url(r'^bulk-create-patients/$', views.BulkCreatePatientView.as_view()),                        # app
            url(r'^get-episodes-for-ids/$', views.EpisodeView.as_view()),                               # app
            url(r'^get-visits-for-user/$', views.GetMyVisits.as_view()),                                # app
            url(r'^get-visits-for-org/(?P<date>\d{4}-\d{2}-\d{2})/$', views.GetVisitsByOrg.as_view()),  # app
            url(r'^get-visits-for-ids/$', views.GetVisitsView.as_view()),                               # app
            url(r'^add-visits/$', views.AddVisitsView.as_view()),                                       # app
            url(r'^delete-visit-for-id/$', views.DeleteVisitView.as_view()),                            # app
            url(r'^update-visit-for-id/$', views.UpdateVisitView.as_view()),                            # app
            url(r'^upload/$', views.upload_file, name='upload'),
            url(r'^get-physician-for-npi/$', views.fetch_physician, name='npi'),                        # admin
            url(r'^create-report-for-visits/$', views.CreateReportForVisits.as_view()),                 # app
            url(r'^get-reports-for-user/$', views.GetReportsForUser.as_view()),                         # app
            url(r'^get-reports-detail-by-ids/$', views.GetReportsDetailByIDs.as_view()),                # app

            # Todo: Endpoints for syncing past data with app - for new installations (version 0.6.0)
            url(r'get-assigned-patients-history', views.AssignedPatientsHistoryDetailView.as_view()),   # app
        ])
    ),
]
