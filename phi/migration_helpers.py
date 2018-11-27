class MigrationHelpers:

    @staticmethod
    def handle_miles_migration(visit_miles):
        odometer_start = visit_miles.get('odometerStart', None)
        odometer_end = visit_miles.get('odometerEnd', None)
        if 'computedMiles' not in visit_miles:
            # Key won't be present for older apps. Handle those
            if odometer_end is not None and odometer_start is not None:
                miles_comments = visit_miles.get('milesComments', '') or ''
                visit_miles['computedMiles'] = float(odometer_end) - float(odometer_start)
                visit_miles['milesComments'] = miles_comments + ' Odometer Start: ' + str(odometer_start) + ' Odometer End :' + str(odometer_end)
