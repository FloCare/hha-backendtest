class InvalidDataForSerializerException(Exception):

    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return "Invalid data passed for serializer : " + str(self.errors)