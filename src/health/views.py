import logging

from django.conf import settings
from django.http import HttpResponse

log = logging.getLogger(__name__)


def health(request):
    # check debug
    if settings.DEBUG:
        log.exception("Debug mode not allowed in production")
        return HttpResponse(
            "Debug mode not allowed in production",
            content_type="text/plain",
            status=500,
        )

    return HttpResponse("Connectivity OK", content_type="text/plain", status=200)
