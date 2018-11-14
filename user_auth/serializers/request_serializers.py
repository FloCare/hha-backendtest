from rest_framework import serializers


class CreateUserRequestSerializer(serializers.Serializer):
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    email = serializers.CharField()
    password = serializers.CharField()
    phone = serializers.CharField(source='contact_no', allow_null=True)
    role = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
