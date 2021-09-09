import os

import requests
from django.conf import settings
from django.http import HttpResponse
from zwaarverkeer.tools import ImmediateHttpResponse


class DecosJoin:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _build_url(self, *args):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS', *args)

    def _get_filters(self, number_plate):
        # TEXT48 = number_plate
        # DFUNCTION = result

        # TODO: also check for the date_from and the date_until of the vergunning
        filters = f"?filter=TEXT48 has '{number_plate}'" \
                  f" and PROCESSED eq 'J'" \
                  f" and DFUNCTION eq 'Verleend'"
        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url):
        return requests.get(url, auth=(self.auth_user, self.auth_pass))

    def has_permit(self, number_plate):
        url = self._build_url(self._get_filters(number_plate))
        response = self._do_request(url)
        if response.status_code != 200:
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))
        return response.json()['count'] >= 1
