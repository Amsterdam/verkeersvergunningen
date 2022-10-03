from django.http import HttpResponse


class ImmediateHttpResponse(Exception):
    """
    This exception is used to interrupt the flow of processing to immediately
    return a custom HttpResponse.
    """
    _response = HttpResponse("Nothing provided.")

    def __init__(self, response):
        self._response = response

    @property
    def response(self):
        return self._response
