import logging
import os
from datetime import timedelta
from enum import Enum

from dateutil import parser
from django.conf import settings
from django.utils import timezone
from odata_request_parser.main import OdataSelectParser, OdataFilterParser

from main.decos import DecosBase

log = logging.getLogger(__name__)


class DecosParams(Enum):
    NUMBER_PLATE = 'text49'  # Number plates should always be without any hyphen (-)
    PERMIT_TYPE = 'text17'  # jaarontheffing / dagontheffing / routeontheffing
    PERMIT_DESCRIPTION = 'subject1'  # omschrijving zaak
    PERMIT_VALID_FROM = 'date6'
    PERMIT_VALID_UNTIL = 'date7'
    PERMIT_PROCESSED = 'processed'  # whether the city has decided on giving or denying the permit
    PERMIT_RESULT = 'dfunction'  # this is whether the permit was given or denied


class DecosZwaarverkeer(DecosBase):
    auth_user = settings.DECOS_BASIC_AUTH_USER
    auth_pass = settings.DECOS_BASIC_AUTH_PASS
    zwaar_verkeer_zaaknr = settings.ZWAAR_VERKEER_ZAAKNUMMER

    def get_permits(self, *, number_plate, passage_at):
        if timezone.is_naive(passage_at):
            passage_at = timezone.make_aware(passage_at)

        valid_from, valid_until = self._get_date_strings(passage_at)
        url = self._build_url()
        params = self._get_params(number_plate=number_plate, valid_from=valid_from, valid_until=valid_until)
        response = self._get(url=url, parameters=params)
        content = response.get('content')
        if not content or not isinstance(content, list):
            return []

        permits = self._interpret_permits(content, passage_at)
        return permits

    def _get_params(self, number_plate, valid_from, valid_until):
        select_parser = OdataSelectParser()
        filter_parser = OdataFilterParser()
        select_parser.add_fields([str(p.value) for p in DecosParams])
        filters = [
            {"_has": {DecosParams.NUMBER_PLATE.value: number_plate}},
            {"_eq": {DecosParams.PERMIT_PROCESSED.value: "J"}},
            {"_eq": {DecosParams.PERMIT_RESULT.value: "Verleend"}},
            {"_le": {DecosParams.PERMIT_VALID_FROM.value: valid_from}},
            {"_ge": {DecosParams.PERMIT_VALID_UNTIL.value: valid_until}},
        ]
        params = {
            "select": select_parser.parse(),
            "filter": filter_parser.parse(filters)
        }
        return params

    def _build_url(self):
        return os.path.join(self.base_url, settings.ZWAAR_VERKEER_ZAAKNUMMER, 'FOLDERS')

    def _interpret_permits(self, content, passage_at):
        permits = []
        for permit_info in content:
            fields = permit_info['fields']
            permit_type = fields.get(DecosParams.PERMIT_TYPE.value)
            permit_description = fields.get(DecosParams.PERMIT_DESCRIPTION.value)
            valid_from = timezone.make_aware(parser.parse(fields[DecosParams.PERMIT_VALID_FROM.value]))
            valid_until = timezone.make_aware(parser.parse(fields[DecosParams.PERMIT_VALID_UNTIL.value]))

            if not permit_type:
                # We have no permit type, so we cannot determine whether this permit is
                # actually valid, AND we cannot determine the correct valid_until time.
                # Therefor we disregard this permit by continuing to the next one.
                continue

            # Set correct validity of the permit: day permits are valid until 06:00 the day after, and year and
            # route permits are valid until the end of the last day (so 00:00:00 the next day)
            valid_until = self._get_valid_until(permit_type=permit_type, valid_until=valid_until)

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

    def _get_valid_until(self, permit_type, valid_until):
        valid_until = (valid_until + timedelta(days=1))
        if 'dagontheffing' in permit_type.lower():
            valid_until = valid_until.replace(hour=6, minute=0, second=0)
        return valid_until

    def _get_date_strings(self, passage_at):
        """
        Get the date string from the passage_at and create a valid from/until
        """
        valid_from = passage_at.date().isoformat()
        # Day permits are valid from 00:00 until 06:00 the day after.
        # So we also get the permits from the day before.
        # That way we can loop over them and check whether they are day permits and if so they are also valid
        valid_until = (passage_at.date() - timedelta(days=1)).isoformat()
        return valid_from, valid_until

