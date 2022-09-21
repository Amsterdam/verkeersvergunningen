import logging
import urllib
from urllib.parse import quote
from datetime import timedelta

import requests
from django.conf import settings
from django.http import HttpResponse
from requests import RequestException

log = logging.getLogger(__name__)


class DecosBase:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _get(self, url, parameters=None):
        """
        Generate a get requests for the given Url and parameters
        """
        try:
            parsed_params = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote)
            response = self._get_response(params=parsed_params, url=url)
            # TODO: account for pagination in the decos join api
            response.raise_for_status()
        except requests.exceptions.ReadTimeout:
            raise ImmediateHttpResponse(response=HttpResponse("Timeout trying to fetch data from Decos", status=504))
        except RequestException as e:
            log.error(f"We got an {e.response.status_code} "
                      f"error from Decos Join saying: {e.response.content}")
            raise ImmediateHttpResponse(response=HttpResponse(
                "We got an error response from Decos Join", status=502))

        return response.json()

    def _get_response(self, params, url):
        response = requests.get(
            url,
            params=params,
            auth=(self.auth_user, self.auth_pass),
            headers={'accept': 'application/itemdata'},
            timeout=5,
        )
        return response

    def _get_date_strings(self, passage_at):
        valid_from = passage_at.date().isoformat()
        # Day permits are valid from 00:00 until 06:00 the day after.
        # So we also get the permits from the day before.
        # That way we can loop over them and check whether they are day permits and if so they are also valid
        valid_until = (passage_at.date() - timedelta(days=1)).isoformat()
        return valid_from, valid_until


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
