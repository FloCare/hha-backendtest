from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'patients', views.AccessiblePatientsViewSet)
# TODO: DISABLE THIS IN PRODUCTION
router.register(r'all', views.AllPatientsViewset)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^my-patients/$', views.AccessiblePatientListView.as_view()),
            url(r'^my-patients-details/$', views.AccessiblePatientsDetailView.as_view())
        ])
    ),
]
