class MigrationHelpers:

    @staticmethod
    def handle_miles_migration(visit_miles):
        odometer_start = visit_miles.get('odometerStart', None)
        odometer_end = visit_miles.get('odometerStart', None)
        if odometer_end is not None and odometer_start is not None:
            visit_miles['computedMiles'] = float(odometer_end) - float(odometer_start)
