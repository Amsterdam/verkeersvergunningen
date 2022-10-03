import base64
import logging

from django.conf import settings
from rest_framework import authentication, exceptions

log = logging.getLogger(__name__)


class BasicAuthWithKeys(authentication.BaseAuthentication):
    def authenticate(self, request):
        basic_credentials = request.META.get('HTTP_AUTHORIZATION')
        if not basic_credentials:
            raise exceptions.AuthenticationFailed('No such user')

        try:
            (username, passw) = base64.b64decode(basic_credentials.replace('Basic ', '')).decode("utf-8").split(':')
            if username != settings.CLEOPATRA_BASIC_AUTH_USER or passw != settings.CLEOPATRA_BASIC_AUTH_PASS:
                raise exceptions.AuthenticationFailed('No such user')
        except Exception as e:
            raise exceptions.AuthenticationFailed('No such user')

        return ('user', None)
