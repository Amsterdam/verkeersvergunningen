import logging
import urllib
import requests

from urllib.parse import quote
from requests import RequestException

from django.conf import settings
from django.http import HttpResponse

from main.exceptions import ImmediateHttpResponse


log = logging.getLogger(__name__)


class DecosBase:
    base_url = settings.DECOS_BASE_URL

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
