class VisitsNotFoundException(Exception):
    def __init__(self, visit_ids):
        self.visit_ids = visit_ids

    def __str__(self):
        return "Visit Ids: " + str(self.visit_ids) + " are not present."
