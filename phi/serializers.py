from rest_framework import serializers
from phi import models
from user_auth import serializers as user_serializers


class PatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Patient
        fields = ('id', 'first_name', 'last_name', 'title', 'dob', 'gender',
                  'primary_contact', 'emergency_contact', 'created_on', 'archived',)
