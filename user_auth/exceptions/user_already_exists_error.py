class UserAlreadyExistsError(Exception):

    def __init__(self, request_data):
        self.request_data = request_data

    def __str__(self):
        return "User already exists with the following data: " + str(self.request_data)