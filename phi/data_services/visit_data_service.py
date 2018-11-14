from phi.exceptions.InvalidDataForSerializerException import InvalidDataForSerializerException
from phi.serializers.serializers import VisitMilesSerializer, VisitSerializer
from phi.migration_helpers import MigrationHelpers


class VisitDataService:

    def __init__(self):
        pass

    def update_visit(self, user_profile, visit, data):
        serializer = VisitSerializer(instance=visit, data=data)
        visit_miles = data.get('visitMiles', {})
        MigrationHelpers.handle_miles_migration(visit_miles)
        visit_miles_serialised_object = VisitMilesSerializer(instance=visit.visit_miles, data=visit_miles)
        if not serializer.is_valid():
            raise InvalidDataForSerializerException(serializer.errors)
        if not visit_miles_serialised_object.is_valid():
            raise InvalidDataForSerializerException(visit_miles_serialised_object.errors)
        serializer.save(user=user_profile)
        visit_miles_serialised_object.save()