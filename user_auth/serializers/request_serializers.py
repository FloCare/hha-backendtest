from rest_framework import serializers


class RequestSerializer(serializers.Serializer):

    def create(self, validated_data):
        # TODO Raise Method Not implemented
        pass

    def update(self, instance, validated_data):
        # TODO Raise Method Not implemented
        pass


class CreateUserRequestSerializer(RequestSerializer):
    firstName = serializers.CharField(source='first_name', required=True)
    lastName = serializers.CharField(source='last_name', required=True)
    email = serializers.CharField()
    password = serializers.CharField()
    phone = serializers.CharField(source='contact_no', allow_null=True)
    role = serializers.CharField()


class UpdateUserRequestSerializer(RequestSerializer):
    firstName = serializers.CharField(source='first_name', required=False)
    lastName = serializers.CharField(source='last_name', required=False)
    email = serializers.CharField(required=False)
    password = serializers.CharField(required=False)
    phone = serializers.CharField(source='contact_no', allow_null=True, required=False)
    role = serializers.CharField(required=False)

