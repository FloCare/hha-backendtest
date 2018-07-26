from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'patients', views.AccessiblePatientViewSet)                                    # admin
router.register(r'physicians', views.PhysiciansViewSet)                                         # admin
# router.register(r'visits', views.VisitsViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^get-assigned-patient-ids/$', views.AccessiblePatientListView.as_view()),     # app
            url(r'^get-patients-for-ids/$', views.AccessiblePatientsDetailView.as_view()),      # app
            url(r'^get-patients-for-old-ids/$', views.GetPatientsByOldIds.as_view()),           # app
            url(r'^get-episodes-for-ids/$', views.EpisodeView.as_view()),                       # app
            url(r'^get-visits-for-user/$', views.GetMyVisits.as_view()),                        # app
            url(r'^get-visits-for-ids/$', views.GetVisitsView.as_view()),                       # app
            url(r'^add-visits/$', views.AddVisitsView.as_view()),                               # app
            url(r'^delete-visit-for-id/$', views.DeleteVisitView.as_view()),                    # app
            url(r'^update-visit-for-id/$', views.UpdateVisitView.as_view()),                    # app
            url(r'^upload/$', views.upload_file, name='upload'),
        ])
    ),
]
