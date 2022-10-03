import os
from enum import Enum
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main.decos import DecosBase, ImmediateHttpResponse
from taxi.enums import DecosFolders, DecosZaaknummers, PermitParams


class DecosTaxi(DecosBase):
    def get_ontheffingen_by_driver_bsn(self, driver_bsn: str) -> list[dict]:
        """
        request the permit from a driver based on their bsn nr
        """
        decos_key = self._get_driver_decos_key(driver_bsn)
        driver_permits = self._get_ontheffingen_by_decos_key(decos_key)
        return driver_permits

    def _get_driver_decos_key(self, driver_bsn: str) -> str:
        """
        Request the decos key from decosdvl for a driver based on their bsn nr
        """

        class DecosParams(Enum):
            bsn = "num1"

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
            folder=DecosFolders.taxi.value,
        )
        data = self._get(url, parameters)
        zaaknummers = self._parse_decos_key(data)
        if not len(zaaknummers) == 1:
            raise ImmediateHttpResponse("Error finding decos_key for that BSN")
        return zaaknummers[0]

    def get_ontheffingen_by_decos_key_driver(self, driver_decos_key):
        url = self._build_url(zaaknummer=driver_decos_key, folder=DecosFolders.folders.value)
        permits = self._get_ontheffingen_by_decos_key(url=url)
        return permits

    def get_ontheffingen_by_decos_key_ontheffing(self, ontheffing_decos_key):
        url = self._build_url(zaaknummer=ontheffing_decos_key, folder='')
        permits = self._get_ontheffingen_by_decos_key(url=url)
        return permits[0]

    def _get_ontheffingen_by_decos_key(self, url):
        driver_permits = self._get_ontheffingen(url)
        for permit in driver_permits:
            zaaknummer = permit[PermitParams.zaakidentificatie.name]
            enforcement_cases = self._get_handhavingzaken(permit_decos_key=zaaknummer)
            permit["schorsingen"] = enforcement_cases
        return driver_permits

    def _get_ontheffingen(self, url: str) -> list[dict]:
        """
        get the documents from the driver based on the drivers key
        """

        class DecosParams(Enum):
            geldigVanaf = "date6"
            geldigTot = "date7"
            afgehandeld = "processed"
            resultaat = "dfunction"
            zaaktype = "text45"

        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        odata_select.add_fields([str(p.value) for p in DecosParams])
        filters = [
            {"_eq": {DecosParams.zaaktype.value: "TAXXXI Zone-ontheffing"}},
            {"_eq": {DecosParams.afgehandeld.value: "true"}},
        ]
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "oDataQuery.select": odata_select.parse(),
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        response = self._get(url, parameters)
        driver_permits = self._parse_decos_permits(response)
        return driver_permits

    def _get_handhavingzaken(self, permit_decos_key: str) -> list[dict]:
        """
        get the enforcement cases from the driver based on the drivers key
        "handhaving" is synonymous for "schorsing" in this code
        """

        class DecosParams(Enum):
            resultaat = "dfunction"
            geldigVanaf = "date6"
            geldigTot = "date7"

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
            folder=DecosFolders.folders.value,
        )
        response = self._get(url, parameters)
        driver_enforcement_cases = self._parse_decos_permits(response)
        return driver_enforcement_cases

    def _parse_decos_key(self, data: dict) -> list[str]:
        try:
            return [c["key"] for c in data["content"]]
        except KeyError as e:
            raise ImmediateHttpResponse(e)

    def _parse_decos_permits(self, data: dict) -> list[dict]:
        try:
            parsed_permits = [
                {
                    PermitParams.zaakidentificatie.name: permit[PermitParams.zaakidentificatie.value],
                    PermitParams.geldigVanaf.name: permit["fields"][PermitParams.geldigVanaf.value],
                    PermitParams.geldigTot.name: permit["fields"][PermitParams.geldigTot.value],
                }
                for permit in data["content"]
            ]
            return parsed_permits
        except KeyError as e:
            raise ImmediateHttpResponse(e)

    def _build_url(self, *, zaaknummer: str, folder: str) -> str:
        return os.path.join(self.base_url, zaaknummer, folder)
