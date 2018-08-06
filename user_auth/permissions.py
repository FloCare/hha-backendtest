from rest_framework import permissions
from user_auth.models import UserOrganizationAccess, UserProfile


class IsAdminForOrg(permissions.BasePermission):
    """
    Permission class to allow only admin users access data
    """
    message = "Admin access needed"

    def has_permission(self, request, view):
        try:
            if UserOrganizationAccess.objects.filter(user__id=request.user.profile.id).filter(is_admin=True).exists():
                return True
        except Exception as e:
            print(str(e))
            return False
        return False


class IsUserActive(permissions.BasePermission):
    """
    Permission class to allow patient relevant data to staff
    """

    def has_permission(self, request, view):
        try:
            if UserOrganizationAccess.objects.filter(user__id=request.user.profile.id).filter(is_active=True).exists():
                return True
        except Exception as e:
            return False
        return False