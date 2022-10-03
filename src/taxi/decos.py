import os
from enum import Enum
from django.conf import settings
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main.decos import DecosBase, ImmediateHttpResponse


class DecosFolders(Enum):
    taxi = "TAXXXI"
    folders = "FOLDERS" # This may seem counterintuitive but a folder is called 'Folders'


class DecosZaaknummers(Enum):
    """
    An enforcement case is a withdrawal of a permit, so if there is a permit and an
    enforcement case for that permit, the permit is invalidated
    """
    bsn: str = settings.TAXI_BSN_ZAAKNUMMER
    zone_ontheffing: str = settings.TAXI_ZONE_ONTHEFFING_ZAAKNUMMER  # Permits
    handhavingszaken: str = settings.TAXI_HANDHAVINGSZAKEN_ZAAKNUMMER  # Enforcement cases


class DecosTaxi(DecosBase):

    def get_taxi_zone_ontheffing(self, driver_bsn: str) -> list[dict]:
        """
        request the permit from a driver based on their bsn nr
        """
        decos_key = self.get_driver_decos_key(driver_bsn)
        driver_permits = self.get_driver_ontheffing_en_handhaving(decos_key)
        return [{'vergunningsnummer': p} for p in driver_permits]

    def get_driver_decos_key(self, driver_bsn: str) -> str:
        """
        Request the decos key from decosdvl for a driver based on their bsn nr
        """

        class DecosParams(Enum):
            bsn = "NUM1"

        odata_filter = OdataFilterParser()
        filters = [{"_eq": {DecosParams.bsn.value: driver_bsn}}]
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "oDataQuery.select": DecosParams.bsn.value,
            "oDataQuery.filter": odata_filter.parse(filters),
        }

        url = self._build_url(
            zaaknummer=DecosZaaknummers.bsn.value,
            endpoint=DecosFolders.taxi.value,
        )
        data = self._get(url, parameters)
        zaaknummers = self._parse_key(data)
        if not len(zaaknummers) == 1:
            raise ImmediateHttpResponse("Error finding decos_key for that BSN")
        return zaaknummers[0]

    def get_driver_ontheffing_en_handhaving(self, driver_decos_key: str) -> list[str]:
        """
        get the documents from the driver based on the drivers key
        """

        class DecosParams(Enum):
            ingangsdatum_ontheffing = "DATE6"
            vervaldatum_ontheffing = "DATE7"
            afgehandeld = "PROCESSED"
            resultaat = "DFUNCTION"
            zaaktype = "TEXT45"

        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        odata_select.add_fields([str(p.value) for p in DecosParams])
        filters = [
            {
                "_or": [
                    {"_eq": {DecosParams.zaaktype.value: "TAXXXI Zone-ontheffing"}},
                    {"_eq": {DecosParams.zaaktype.value: "TAXXXI Handhaving"}},
                ]
            }
        ]
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "oDataQuery.select": odata_select.parse(),
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        url = self._build_url(
            zaaknummer=driver_decos_key, endpoint=DecosFolders.folders.value
        )
        response = self._get(url, parameters)
        driver_permits = self._parse_key(response)
        return driver_permits

    def get_handhavingzaken(self, permit_decos_key: str) -> list[str]:
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
            "properties": "false",
            "fetchParents": "false",
            "relTypeKey": permit_decos_key,
            "oDataQuery.select": odata_select.parse(),
        }
        url = self._build_url(
            zaaknummer=DecosZaaknummers.handhavingszaken.value,
            endpoint=DecosFolders.folders.value,
        )
        data = self._get(url, parameters)
        return data

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
