from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'patients', views.AccessiblePatientViewSet)
router.register(r'physicians', views.PhysiciansViewSet)
router.register(r'visits', views.VisitsViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^get-assigned-patient-ids/$', views.AccessiblePatientListView.as_view()),     # app
            url(r'^get-patients-for-ids/$', views.AccessiblePatientsDetailView.as_view()),      # app
            url(r'^get-episodes-for-ids/$', views.EpisodeView.as_view()),                       # app
            url(r'^upload/$', views.upload_file, name='upload'),
            # url('visits/$', views.add_visit, name='add_visit')
        ])
    ),
]
