from django.conf.urls import url, include

from user_auth import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'', views.UserViewSet)

urlpatterns = [
    url(r'^v1.0/', include([
            url(r'^', include(router.urls)),
        ])
    ),
]
