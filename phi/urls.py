from django.conf.urls import url, include

from phi import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# Todo: Allow only get request in this API
# router.register(r'patients', views.AccessiblePatientsViewSet)
router.register(r'patients', views.AccessiblePatientViewSet)
# TODO: DISABLE THIS IN PRODUCTION
# router.register(r'all', views.AllPatientsViewset)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            # url(r'patients/add/', views.AddPatientView),
            url(r'^my-patients/$', views.AccessiblePatientListView.as_view()),
            url(r'^my-patients-details/$', views.AccessiblePatientsDetailView.as_view())
        ])
    ),
]
