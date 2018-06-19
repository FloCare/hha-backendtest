from django.conf.urls import url, include

from user_auth import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'org-access', views.UserOrganizationView.as_view()),
            url(r'profile', views.UserProfileView.as_view()),
        ])
    ),
]
