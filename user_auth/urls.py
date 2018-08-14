from django.conf.urls import url, include

from user_auth import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# router.register(r'profile', views.UserProfileViewSet)
router.register(r'staff', views.UsersViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
            url(r'^get-user-for-id/$', views.UserProfileView.as_view()),                  # app
            url(r'org-access', views.UserOrganizationView.as_view()),
        ])
    ),
]
