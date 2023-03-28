import logging
import urllib

import requests
from django.conf import settings
from django_http_exceptions import HTTPExceptions
from requests import JSONDecodeError

log = logging.getLogger(__name__)


class DecosBase:
    base_url = settings.DECOS_BASE_URL

    def _get(self, url, parameters=None):
        """
        Generate a get requests for the given Url and parameters
        """
        try:
            parsed_params = urllib.parse.urlencode(
                parameters, quote_via=urllib.parse.quote
            )
            response = self._get_response(params=parsed_params, url=url)
            # TODO: account for pagination in the decos join api
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise HTTPExceptions.SERVICE_UNAVAILABLE.with_content(
                "Unable to reach Decos server"
            )
        except requests.exceptions.ReadTimeout:
            raise HTTPExceptions.GATEWAY_TIMEOUT.with_content(
                "Timeout trying to fetch data from Decos"
            )
        except requests.exceptions.RequestException as e:
            if e.response:
                log.error(
                    f"We got an {e.response.status_code} "
                    f"error from Decos Join saying: {e.response.content}"
                )
            else:
                log.error("No response received from Decos")
            raise HTTPExceptions.BAD_GATEWAY.with_content(
                "We got an error response from Decos"
            )

        try:
            data = response.json()
        except JSONDecodeError:
            raise HTTPExceptions.NOT_FOUND.with_content(
                f"Decos responded with error: {response.content}"
            )
        return data

    def _get_response(self, params, url):
        response = requests.get(
            url,
            params=params,
            auth=(self.auth_user, self.auth_pass),
            headers={"accept": "application/itemdata"},
            timeout=5,
        )
        return response
