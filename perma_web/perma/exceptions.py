# Custom exceptions

class BrokenURLError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class BadFiletypeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class InvalidTransmissionException(Exception):
    pass

class PermaPaymentsCommunicationException(Exception):
    pass

class WebrecorderException(Exception):
    pass
