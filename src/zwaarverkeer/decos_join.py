import os
from datetime import time, timedelta

import requests
from dateutil import parser
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import is_aware, is_naive, make_aware

from zwaarverkeer.tools import ImmediateHttpResponse


DECOS_NUMBER_PLATE = 'text48'  # Always without any hyphen (-)
DECOS_PERMIT_TYPE = 'text17'  # jaarontheffing / dagontheffing / routeontheffing
DECOS_PERMIT_DESCRIPTION = 'subject1'  # omschrijving zaak
DECOS_PERMIT_VALID_FROM = 'date6'
DECOS_PERMIT_VALID_UNTIL = 'date7'
DECOS_PERMIT_PROCESSED = 'processed'  # whether the city has decided on giving or denying the permit
DECOS_PERMIT_RESULT = 'dfunction'  # this is whether the permit was given or denied


class DecosJoin:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _build_url(self, *args):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS', *args)

    def _get_filters(self, number_plate, valid_from, valid_until):
        filters = f"?select={DECOS_NUMBER_PLATE},{DECOS_PERMIT_TYPE},{DECOS_PERMIT_DESCRIPTION},{DECOS_PERMIT_VALID_FROM},{DECOS_PERMIT_VALID_UNTIL}" \
                  f"&filter={DECOS_NUMBER_PLATE} has '{number_plate}'" \
                  f" and {DECOS_PERMIT_PROCESSED} eq 'J'" \
                  f" and {DECOS_PERMIT_RESULT} eq 'Verleend'" \
                  f" and {DECOS_PERMIT_VALID_FROM} le '{valid_from}'" \
                  f" and {DECOS_PERMIT_VALID_UNTIL} ge '{valid_until}'"
        filters.replace(' ', '%20')
        return filters

    def _do_request(self, url, is_item=False):
        return requests.get(
            url,
            auth=(self.auth_user, self.auth_pass),
            headers={'accept': 'application/itemdata'})

    def _get_date_strings(self, passage_at, before_6_oclock):
        valid_from = valid_until = passage_at.date().isoformat()
        if before_6_oclock:
            # Day permits are valid from 00:00 until 06:00 the day after.
            # So if the passage_at is before 06:00, we also get the permits from the day before.
            # That way we can loop over them and check whether they are day permits and if so they are also valid
            valid_until = (passage_at.date() - timedelta(days=1)).isoformat()
        return valid_from, valid_until

    def get_permits(self, number_plate, passage_at):
        before_6_oclock = passage_at.time() < time(6)
        valid_from, valid_until = self._get_date_strings(passage_at, before_6_oclock)
        url = self._build_url(self._get_filters(number_plate, valid_from, valid_until))
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
            permit_type = fields.get(DECOS_PERMIT_TYPE)
            permit_description = fields.get(DECOS_PERMIT_DESCRIPTION)
            valid_from = make_aware(parser.parse(fields[DECOS_PERMIT_VALID_FROM]))
            valid_until = make_aware(parser.parse(fields[DECOS_PERMIT_VALID_UNTIL]))

            permit_dict = {
                'permit_type': permit_type,
                'permit_description': permit_description,
                'valid_from': valid_from,
                'valid_until': valid_until,
            }

            # Check whether this permit is valid for the passage
            if not before_6_oclock:
                # We only fetched the valid permits for today from decos join, so any permit will do
                permits.append(permit_dict)
            else:
                if not permit_type and valid_until.date() < passage_at.date():
                    # We cannot be sure whether this permit is valid, so we don't return it
                    continue

                # We fetched all permits which are valid from today, and until yesterday. So for every permit we
                # need to check whether it is valid for the passage by combining its type, valid_from and valid_until
                # with the passage_at.
                if 'dagontheffing' in permit_type.lower():
                    # A day permit for today or yesterday is valid, so we'll continue
                    permits.append(permit_dict)
                elif any(_type in permit_type.lower() for _type in ('jaarontheffing', 'routeontheffing')) \
                    and valid_from.date() <= passage_at.date() \
                    and valid_until.date() >= passage_at.date():
                    permits.append(permit_dict)

        # TODO: Do we need to enrich valid_from and valid_until so that the times are correctly reflected?
        # This means making day permits valid until the next day 06:00 and making the other permits valid
        # until 23:59 at the last day
        # Discuss with Cleopatra people

        return permits
