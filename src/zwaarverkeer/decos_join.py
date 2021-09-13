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

    def _get_filters(self, number_plate, passage_at):
        # TEXT48 = number_plate
        # TEXT17 = type ontheffing (jaarontheffing/dagontheffing/routeontheffing)
        # DFUNCTION = result
        # DATE6 = date from
        # DATE7 = date until

        filters = f"?filter=TEXT48 has '{number_plate}'" \
                  f" and PROCESSED eq 'J'" \
                  f" and DFUNCTION eq 'Verleend'" \
                  f" and DATE6 le '{passage_at.date().isoformat()}'" \
                  f" and DATE7 ge '{passage_at.date().isoformat()}'"
        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url):
        return requests.get(url, auth=(self.auth_user, self.auth_pass))

    def has_permit(self, number_plate, passage_at):
        url = self._build_url(self._get_filters(number_plate, passage_at))
        response = self._do_request(url)
        if response.status_code != 200:
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))

        # TODO:
        # Dagvergunningen are also valid until 06:00 the day after.
        # So if the passage_at is before 06:00, also get the vergunningen from the day before,
        # loop over them and check whether they are dagvergunningen and if so they are also valid.

        if not response.json().get('count'):
            return False

        # TODO: get the "soort vergunning" and also return that (dagontheffing/jaarontheffing/routeontheffing)
        # TODO: in case more than one vergunning is valid, which one should be returned?

        return True
