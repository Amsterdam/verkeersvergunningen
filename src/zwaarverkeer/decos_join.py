import os
from datetime import time, timedelta

import requests
from dateutil import parser
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

    def _get_filters(self, number_plate, date_from, date_until):
        # TEXT48 = number_plate
        # TEXT17 = type ontheffing (jaarontheffing/dagontheffing/routeontheffing)
        # SUBJECT1 = omschrijving zaak
        # DATE6 = date from
        # DATE7 = date until
        # DFUNCTION = result

        filters = f"?select=text48,text17,subject1,date6,date7" \
                  f"&filter=text48 has '{number_plate}'" \
                  f" and processed eq 'J'" \
                  f" and dfunction eq 'Verleend'" \
                  f" and date6 le '{date_from}'" \
                  f" and date7 ge '{date_until}'"

        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url, is_item=False):
        return requests.get(
            url,
            auth=(self.auth_user, self.auth_pass),
            headers={'accept': 'application/itemdata'})

    def _get_date_strings(self, passage_at, before_6):
        date_from = date_until = passage_at.date().isoformat()
        if before_6:
            # Day permits are valid from 00:00 until 06:00 the day after.
            # So if the passage_at is before 06:00, we also get the permits from the day before.
            # That way we can loop over them and check whether they are day permits and if so they are also valid
            date_until = (passage_at.date() - timedelta(days=1)).isoformat()
        return date_from, date_until

    def get_permits(self, number_plate, passage_at):
        before_6 = passage_at.time() < time(6)
        date_from, date_until = self._get_date_strings(passage_at, before_6)
        url = self._build_url(self._get_filters(number_plate, date_from, date_until))
        response = self._do_request(url)
        if response.status_code != 200:
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))

        response_json = response.json()

        permits = []  # a temporary list to get the permits
        if not response_json.get('count'):
            return permits

        # Loop over te permits and get the details
        for permit_info in response_json['content']:
            fields = permit_info['fields']
            permit_type = fields.get('text17')
            permit_description = fields.get('subject1')
            valid_from = fields['date6']
            valid_until = fields['date7']

            permit_dict = {
                'permit_type': permit_type,
                'permit_description': permit_description,
                'valid_from': valid_from,
                'valid_until': valid_until,
            }

            # Check whether this permit is valid for the passage
            if not before_6:
                # We only fetched the valid permits for today from decos join, so any permit will do
                permits.append(permit_dict)
            else:
                if not permit_type:
                    # We cannot be sure whether this permit is valid, so we don't return it
                    continue

                # We fetched all permits which are valid from today, and until yesterday. So for every permit we
                # need to check whether it is valid for the passage by combining its type, valid_from and valid_until
                # with the passage_at.
                if 'dagontheffing' in permit_type.lower():
                    # A day permit for today or yesterday is valid, so we'll continue
                    permits.append(permit_dict)
                elif any(_type in permit_type.lower() for _type in ('jaarontheffing', 'routeontheffing')) \
                    and parser.parse(valid_from).date() <= passage_at.date() \
                    and parser.parse(valid_until).date() >= passage_at.date():
                    permits.append(permit_dict)

        return permits
