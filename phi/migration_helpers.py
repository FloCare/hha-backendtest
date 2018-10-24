class MigrationHelpers:

    @staticmethod
    def handle_miles_migration(visit_miles):
        odometer_start = visit_miles.get('odometerStart', None)
        odometer_end = visit_miles.get('odometerEnd', None)
        miles_comments = visit_miles.get('milesComments', '')
        if odometer_end is not None and odometer_start is not None:
            visit_miles['computedMiles'] = float(odometer_end) - float(odometer_start)
            visit_miles['milesComments'] = miles_comments + ' Odometer Start: ' + str(odometer_start) + ' Odometer End :' + str(odometer_end)
