from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'patients', views.AccessiblePatientViewSet)
router.register(r'physicians', views.PhysiciansViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^my-patients/$', views.AccessiblePatientListView.as_view()),
            url(r'^my-patients-details/$', views.AccessiblePatientsDetailView.as_view()),
            url(r'^episodes/$', views.EpisodeViewSet.as_view()),
            url(r'^upload/$', views.upload_file, name='upload'),
            url('visits/$', views.add_visit, name='add_visit')
        ])
    ),
]
