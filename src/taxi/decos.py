import os
from enum import Enum
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main import settings
from main.decos import DecosBase
from taxi.enums import DecosFolders, DecosZaaknummers, PermitParams
from django_http_exceptions import HTTPExceptions


class DecosTaxi(DecosBase):
    auth_user = settings.DECOS_TAXI_AUTH_USER
    auth_pass = settings.DECOS_TAXI_AUTH_PASS

    def get_ontheffingen_by_driver_bsn(self, driver_bsn: str) -> list[dict]:
        """
        request the permit from a driver based on their bsn nr
        """
        decos_key = self._get_driver_decos_key(driver_bsn)
        driver_permits = self.get_ontheffingen_by_decos_key_driver(decos_key)
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
            raise HTTPExceptions.NOT_FOUND.with_content("Error finding decos_key for that BSN")
        return zaaknummers[0]

    def get_ontheffingen_by_decos_key_driver(self, driver_decos_key):
        driver_permits = self._get_ontheffingen_driver(driver_decos_key=driver_decos_key)
        for permit in driver_permits:
            self._add_enforcement_cases_to_permit_data(permit)
        return driver_permits

    def _get_ontheffingen_driver(self, driver_decos_key: str) -> list[dict]:
        """
        get the documents from the driver based on the drivers key
        """
        url = self._build_url(zaaknummer=driver_decos_key, folder=DecosFolders.folders.value)
        response = self._get_ontheffing(url)
        driver_permits = self._parse_decos_permits(response)
        return driver_permits

    def get_ontheffing_by_decos_key_ontheffing(self, ontheffing_decos_key: str) -> dict:
        permit = self._get_ontheffing_details(ontheffing_decos_key=ontheffing_decos_key)
        self._add_enforcement_cases_to_permit_data(permit)
        return permit

    def _get_ontheffing_details(self, ontheffing_decos_key: str) -> dict:
        """
        get the documents from the driver based on the drivers key
        """
        url = self._build_url(zaaknummer=ontheffing_decos_key, folder='')
        response = self._get_ontheffing(url)
        permit = self._parse_permit(response)
        return permit

    def _get_ontheffing(self, url: str):
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
        return response

    def _add_enforcement_cases_to_permit_data(self, permit: dict):
        zaaknummer = permit[PermitParams.zaakidentificatie.name]
        enforcement_cases = self._get_handhavingzaken(permit_decos_key=zaaknummer)
        print(enforcement_cases)
        permit["schorsingen"] = enforcement_cases

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
        if data == "Not Found" or not data.get("content"):
            raise HTTPExceptions.NO_CONTENT.with_content("No data found in Decos for that query")
        try:
            return [c["key"] for c in data["content"]]
        except KeyError:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the response from Decos")

    def _parse_decos_permits(self, data: dict) -> list[dict]:
        if data == "Not Found" or not data.get("content"):
            raise HTTPExceptions.NO_CONTENT.with_content("No data found in Decos for that query")
        try:
            parsed_permits = [
                self._parse_permit(permit)
                for permit in data["content"]
            ]
            return parsed_permits
        except KeyError:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the response from Decos")

    def _parse_permit(self, permit: dict) -> dict:
        return {
            PermitParams.zaakidentificatie.name: permit[PermitParams.zaakidentificatie.value],
            PermitParams.geldigVanaf.name: permit["fields"][PermitParams.geldigVanaf.value],
            PermitParams.geldigTot.name: permit["fields"][PermitParams.geldigTot.value],
        }

    def _build_url(self, *, zaaknummer: str, folder: str) -> str:
        return os.path.join(self.base_url, zaaknummer, folder)
