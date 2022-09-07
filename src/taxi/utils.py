import os
from enum import Enum
from django.conf import settings
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main.decos_join import DecosJoin
from main.tools import ImmediateHttpResponse


class DecosBusiness(Enum):
    taxi = "TAXXXI"
    folders = "FOLDERS"


class DecosParams(Enum):
    resultaat = "DFUNCTION"
    afgehandeld = "PROCESSED"
    ingangsdatum_ontheffing = "DATE6"
    vervaldatum_ontheffing = "DATE7"
    zaaktype = "TEXT45"


class DecosTaxi(DecosJoin):
    taxi_zaaknr = {
        "bsn": settings.TAXI_BSN_ZAAKNR,
        "permit": settings.TAXI_PERMIT_ZAAKNR,
    }

    def get_taxi_permit(self, bsn: str):
        """
        request the permit from a driver based on their bsn nr
        """
        decos_key = self.get_decos_key(bsn)
        driver_permit = self.get_driver_permit(decos_key)
        return driver_permit

    def get_decos_key(self, driver_bsn: str) -> str:
        """
        Request the decos key from decosdvl for a driver based on their bsn nr
        """
        parameters = {
            "properties": False,
            "oDataQuery.filter": f"TEXT13%20eq%{driver_bsn}",
        }

        url = self._build_url("bsn", DecosBusiness.taxi.value)
        response = self._get(url, parameters)
        return self.parse_decos_key_response(response)

    def parse_decos_key_response(self, data: dict) -> str:
        """
        Get the decos key from the response data
        """
        try:
            return data["content"][0]["key"]
        except (KeyError, IndexError) as e:
            raise ImmediateHttpResponse

    def get_driver_permit(self, driver_key: str):
        """
        get the documents from the driver based on the drivers key
        """
        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        odata_select.add_fields([str(d.value) for d in DecosParams])
        filters = [
            {
                "_or": [
                    {"_has": {DecosParams.zaaktype.value: "zone"}},
                    {"_has": {DecosParams.zaaktype.value: "lijnbus"}},
                ]
            }
        ]
        parameters = {
            "properties": False,
            "fetchParents": False,
            "oDataQuery.select": odata_select.parse(),
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        url = self._build_url("permit", DecosBusiness.folders.value)
        response = self._get(url, parameters)
        permit = response.json().get("files?")
        return permit

    def _build_url(self, business_id: str, busines_name: str) -> str:
        return os.path.join(
            self.base_url, self.taxi_zaaknr.get(business_id), busines_name
        )
