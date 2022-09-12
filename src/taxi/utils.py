import os
from enum import Enum
from django.conf import settings
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main.utils import DecosBase, ImmediateHttpResponse


class DecosBusiness(Enum):
    taxi = "TAXXXI"
    folders = "FOLDERS"


class DecosTaxi(DecosBase):
    ZAAKNUMMER = {
        "BSN": settings.TAXI_BSN_ZAAKNUMMER,
        "ZONE_ONTHEFFING": settings.TAXI_ZONE_ONTHEFFING_ZAAKNUMMER,
        "HANDHAVINGSZAKEN": settings.TAXI_HANDHAVINGSZAKEN_ZAAKNUMMER,
    }

    def get_taxi_permit(self, bsn: str):
        """
        request the permit from a driver based on their bsn nr
        """
        decos_key = self.get_decos_key(bsn)
        driver_permits = self.get_driver_permits(decos_key)
        return driver_permits

    def get_decos_key(self, driver_bsn: str) -> str:
        """
        Request the decos key from decosdvl for a driver based on their bsn nr
        """

        class DecosParams(Enum):
            bsn = "NUM1"
            a_nummer = "TEXT13"

        odata_filter = OdataFilterParser()
        filters = [{"_eq": {DecosParams.bsn.value: driver_bsn}}]
        parameters = {
            "properties": False,
            "fetchParents": False,
            "oDataQuery.select": DecosParams.bsn.value,
            "oDataQuery.filter": odata_filter.parse(filters),
        }

        url = self._build_url(
            zaaknummer=self.ZAAKNUMMER.get("BSN"),
            endpoint=DecosBusiness.taxi.value,
        )
        data = self._get(url, parameters)
        zaaknummers = self._parse_key(data)
        if not len(zaaknummers) == 1:
            raise ImmediateHttpResponse("Error finding decos_key for that BSN")
        return zaaknummers[0]

    def get_driver_permits(self, driver_decos_key: str) -> list[str]:
        """
        get the documents from the driver based on the drivers key
        """

        class DecosParams(Enum):
            resultaat = "DFUNCTION"
            afgehandeld = "PROCESSED"
            ingangsdatum_ontheffing = "DATE6"
            vervaldatum_ontheffing = "DATE7"
            zaaktype = "TEXT45"

        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        odata_select.add_fields([str(p.value) for p in DecosParams])
        filters = [
            {
                "_or": [
                    {"_eq": {DecosParams.zaaktype.value, "TAXXXI Zone-ontheffing"}},
                    {"_eq": {DecosParams.zaaktype.value: "TAXXXI Handhaving"}},
                ]
            }
        ]
        parameters = {
            "properties": False,
            "fetchParents": False,
            "oDataQuery.select": odata_select.parse(),
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        url = self._build_url(
            zaaknummer=driver_decos_key, endpoint=DecosBusiness.folders.value
        )
        response = self._get(url, parameters)
        driver_permits = self._parse_key(response)
        return driver_permits

    def get_driver_exemption(self, driver_bsn: str) -> list[str]:
        """
        get the permits from the driver based on the drivers key
        """

        class DecosParams(Enum):
            bsn = "NUM2"
            resultaat = "DFUNCTION"
            ingangsdatum_ontheffing = "DATE6"
            vervaldatum_ontheffing = "DATE7"

        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        odata_select.add_fields([str(p.value) for p in DecosParams])
        filters = [{"_eq": {DecosParams.bsn.value, driver_bsn}}]
        parameters = {
            "properties": False,
            "fetchParents": False,
            "oDataQuery.select": odata_select.parse(),
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        url = self._build_url(
            zaaknummer=self.ZAAKNUMMER["ZONE_ONTHEFFING"],
            endpoint=DecosBusiness.folders.value,
        )
        data = self._get(url, parameters)
        driver_exemptions = self._parse_key(data)
        return driver_exemptions

    def get_enforcement_cases(self, license_casenr: str) -> list[str]:
        """
        get the cases from the driver based on the drivers key
        """
        class DecosParams(Enum):
            resultaat = "DFUNCTION"
            ingangsdatum_ontheffing = "DATE6"
            vervaldatum_ontheffing = "DATE7"

        odata_select = OdataSelectParser()
        odata_select.add_fields([str(p.value) for p in DecosParams])
        parameters = {
            "properties": False,
            "fetchParents": False,
            "relTypeKey": license_casenr,
            "oDataQuery.select": odata_select.parse(),
        }
        url = self._build_url(
            zaaknummer=self.ZAAKNUMMER["HANDHAVINGSZAKEN"],
            endpoint=DecosBusiness.folders.value,
        )
        data = self._get(url, parameters)
        cases = self._parse_key(data)
        return cases

    def _parse_key(self, data: dict) -> list[str]:
        """
        Get the decos key from the response data
        """
        try:
            return [c["key"] for c in data["content"]]
        except KeyError as e:
            raise ImmediateHttpResponse(e)

    def _build_url(self, *, zaaknummer: str, endpoint: str) -> str:
        return os.path.join(self.base_url, zaaknummer, endpoint)
