class InvalidPayloadError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "Invalid Payload. Errors : " + self.message
