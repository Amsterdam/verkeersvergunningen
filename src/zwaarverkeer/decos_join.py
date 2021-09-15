import os

import requests
from django.conf import settings
from django.http import HttpResponse
from zwaarverkeer.tools import ImmediateHttpResponse
from datetime import time, timedelta

class DecosJoin:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _build_url(self, *args):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS', *args)

    def _get_filters(self, number_plate, date_from, date_until):
        # TEXT48 = number_plate
        # TEXT17 = type ontheffing (jaarontheffing/dagontheffing/routeontheffing)
        # DFUNCTION = result
        # DATE6 = date from
        # DATE7 = date until

        filters = f"?filter=TEXT48 has '{number_plate}'" \
                  f" and PROCESSED eq 'J'" \
                  f" and DFUNCTION eq 'Verleend'" \
                  f" and DATE6 le '{date_from}'" \
                  f" and DATE7 ge '{date_until}'"
        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url, is_item=False):
        headers = {}
        if is_item:
            headers['accept'] = 'application/itemdata'
        return requests.get(url, auth=(self.auth_user, self.auth_pass), headers=headers)

    def _get_date_strings(self, passage_at, before_6):
        date_from = date_until = passage_at.date().isoformat()
        if before_6:
            # Day permits are also valid until 06:00 the day after.
            # So if the passage_at is before 06:00, we also get the permits from the day before.
            # That way we can loop over them and check whether they are day permits and if so they are also valid
            date_from = (passage_at.date() - timedelta(days=1)).isoformat()
        return date_from, date_until

    def get_permit(self, number_plate, passage_at):
        before_6 = passage_at.time() < time(6)
        date_from, date_until = self._get_date_strings(passage_at, before_6)
        url = self._build_url(self._get_filters(number_plate, date_from, date_until))
        response = self._do_request(url)
        if response.status_code != 200:
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))

        response_json = response.json()

        has_permit = False
        permit_type = None
        if not response_json.get('count'):
            return has_permit, permit_type

        if not before_6:
            # The passage was after six, so we queried for all permits valid on the
            # day of passage, so any passage will do
            has_permit = True

        # # Loop over te permits and get the details
        # for permit_info in response_json['content']:
        #     # TODO: put this stuff in a separate function
        #     response = self._do_request(permit_info['links'][0]['href'], is_item=True)
        #     item_response_json = response.json()
        #
        #     if not before_6:
        #         permit_type = item_response_json['fields']['text17']
        #         break
        #
        #     if item_response_json['fields']['text17'].lower().contains('dagontheffing'):
        #         # TODO: Check whether it is valid yesterday
        #         pass


        # TODO: get the "soort vergunning" and also return that (dagontheffing/jaarontheffing/routeontheffing)
        # TODO: in case more than one vergunning is valid, which one should be returned?

        return has_permit, permit_type
