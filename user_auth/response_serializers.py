from rest_framework import serializers
from user_auth import models


class UserProfileResponseSerializer(serializers.ModelSerializer):
    userID = serializers.UUIDField(source='uuid')
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    username = serializers.CharField(source='user.username')
    contactNo = serializers.CharField(source='contact_no')

    class Meta:
        model = models.UserProfile
        fields = ('userID', 'firstName', 'lastName', 'username', 'contactNo', 'address')
