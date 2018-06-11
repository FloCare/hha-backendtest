from django.conf.urls import url, include

from user_auth import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'', views.UserViewSet)
router.register(r'profile', views.UserProfileViewSet)
router.register(r'address', views.AddressViewSet)
router.register(r'org', views.OrganizationViewSet)
router.register(r'org-access', views.UserOrganizationViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
        ])
    ),
]
