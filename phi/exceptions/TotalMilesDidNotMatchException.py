class TotalMilesDidNotMatchException(Exception):
    def __init__(self, total_miles_app, total_miles_db):
        self.total_miles_app = total_miles_app
        self.total_miles_db = total_miles_db

    def __str__(self):
        return "Total miles from app: " + str(self.total_miles_app) + " did not match with values in db : " + str(self.total_miles_db)
