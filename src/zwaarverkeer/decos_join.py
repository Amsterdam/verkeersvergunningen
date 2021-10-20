import logging
import os
from datetime import time, timedelta

import requests
from dateutil import parser
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import is_naive, make_aware

from zwaarverkeer.tools import ImmediateHttpResponse

DECOS_NUMBER_PLATE = 'text49'  # Number plates should always be without any hyphen (-)
DECOS_PERMIT_TYPE = 'text17'  # jaarontheffing / dagontheffing / routeontheffing
DECOS_PERMIT_DESCRIPTION = 'subject1'  # omschrijving zaak
DECOS_PERMIT_VALID_FROM = 'date6'
DECOS_PERMIT_VALID_UNTIL = 'date7'
DECOS_PERMIT_PROCESSED = 'processed'  # whether the city has decided on giving or denying the permit
DECOS_PERMIT_RESULT = 'dfunction'  # this is whether the permit was given or denied

log = logging.getLogger(__name__)


class DecosJoin:
    def __init__(self):
        self.base_url = settings.DECOS_BASE_URL
        self.zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER
        self.auth_user = settings.DECOS_BASIC_AUTH_USER
        self.auth_pass = settings.DECOS_BASIC_AUTH_PASS

    def _build_url(self, *args):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS', *args)

    def _get_filters(self, number_plate, valid_from, valid_until):
        # TODO: Use https://docs.djangoproject.com/en/3.2/ref/request-response/#querydict-objects
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
            headers={'accept': 'application/itemdata'},
            timeout=5,
        )

    def _get_date_strings(self, passage_at):
        valid_from = passage_at.date().isoformat()
        # Day permits are valid from 00:00 until 06:00 the day after.
        # So we also get the permits from the day before.
        # That way we can loop over them and check whether they are day permits and if so they are also valid
        valid_until = (passage_at.date() - timedelta(days=1)).isoformat()
        return valid_from, valid_until

    def get_permits(self, number_plate, passage_at):
        if is_naive(passage_at):
            passage_at = make_aware(passage_at)

        valid_from, valid_until = self._get_date_strings(passage_at)
        url = self._build_url(self._get_filters(number_plate, valid_from, valid_until))
        response = self._do_request(url)

        # TODO: account for pagination in the decos join api

        # TODO: Account for more errors than just "not a 200". Use response.raise_for_status() and
        # TODO: add a try/except around _do_request() call
        if response.status_code != 200:
            log.error(f"We got an {response.status_code} error from Decos Join saying: {response.content}")
            raise ImmediateHttpResponse(response=HttpResponse("We got an error response from Decos Join", status=502))

        permits = []  # a temporary list to get the permits
        content = response.json().get('content')

        if not content or not isinstance(content, list):
            return permits

        # Loop over te permits and get the details
        for permit_info in content:
            fields = permit_info['fields']
            permit_type = fields.get(DECOS_PERMIT_TYPE)
            permit_description = fields.get(DECOS_PERMIT_DESCRIPTION)
            valid_from = make_aware(parser.parse(fields[DECOS_PERMIT_VALID_FROM]))
            valid_until = make_aware(parser.parse(fields[DECOS_PERMIT_VALID_UNTIL]))

            if not permit_type:
                # We have no permit type so we cannot determine whether this permit is
                # actually valid, AND we cannot determine the correct valid_until time.
                # Therefore we disregard this permit by continuing to the next one.
                continue

            # Set correct validity of the permit: day permits are valid until 06:00 the day after, and year and
            # route permits are valid until the end of the last day (so 00:00:00 the next day)
            valid_until = (valid_until + timedelta(days=1))
            if 'dagontheffing' in permit_type.lower():
                valid_until = valid_until.replace(hour=6, minute=0, second=0)

            # Check whether this permit is valid for the passage
            if passage_at >= valid_from and passage_at < valid_until:
                permit_dict = {
                    'permit_type': permit_type,
                    'permit_description': permit_description,
                    'valid_from': valid_from,
                    'valid_until': valid_until,
                }
                permits.append(permit_dict)

        return permits
