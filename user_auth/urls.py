from django.urls import path

from user_auth import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    # User Profile
    path('v1.0/get-user-for-id/', views.UserProfileView.as_view(), name='get-user-for-id'),               # app

    # Staff
    path('v1.0/create-staff/', views.CreateStaffView.as_view(), name='create-staff'),                     # admin
    path('v1.0/get-staff-for-id/<uuid:pk>/', views.GetStaffView.as_view(), name='get-staff'),             # admin
    path('v1.0/update-staff-for-id/<uuid:pk>/', views.UpdateStaffView.as_view(), name='update-staff'),    # admin
    path('v1.0/delete-staff-for-id/<uuid:pk>/', views.DeleteStaffView.as_view(), name='delete-staff'),    # admin

    # Org access
    path('v1.0/org-access/', views.UserOrganizationView.as_view(), name='org-access')                      # admin
]
