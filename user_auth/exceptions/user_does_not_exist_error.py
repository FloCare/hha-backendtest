class UserDoesNotExistError(Exception):

    def __init__(self, user_id):
        self.user_id = user_id

    def __str__(self):
        return "User does not exist for id : " + str(self.user_id)