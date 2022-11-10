import os
from datetime import datetime, timedelta
from enum import Enum
from odata_request_parser.main import OdataFilterParser, OdataSelectParser

from main import settings
from main.decos import DecosBase
from taxi.enums import DecosFolders, DecosZaaknummers, PermitParams
from django_http_exceptions import HTTPExceptions


class DecosTaxi(DecosBase):
    auth_user = settings.DECOS_TAXI_AUTH_USER
    auth_pass = settings.DECOS_TAXI_AUTH_PASS

    def _add_enforcement_cases_to_permit_data(self, permit: dict):
        zaaknummer = permit.pop(PermitParams.zaakidentificatie.name)
        enforcement_cases_data = self._get_handhavingzaken(permit_decos_key=zaaknummer)
        enforcement_cases = self._parse_decos_enforcement_cases(enforcement_cases_data)
        permit["schorsingen"] = enforcement_cases

    def _get_handhavingzaken(self, permit_decos_key: str) -> dict:
        """
        get the enforcement cases from the driver based on the drivers key
        "handhaving" is synonymous for "schorsing" in this code
        """
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "relTypeKey": permit_decos_key,
        }
        url = self._build_url(
            zaaknummer=DecosZaaknummers.handhavingszaken.value,
            folder=DecosFolders.folders.value,
        )
        data = self._get(url, parameters)
        return data

    def _parse_decos_enforcement_cases(self, data: dict) -> list[dict]:
        try:
            parsed_permits = [
                self._parse_enforcement_case(permit)
                for permit in data["content"]
            ]
            return parsed_permits
        except KeyError:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the handhaving from Decos")

    def _parse_enforcement_case(self, permit: dict) -> dict:
        return {
            PermitParams.zaakidentificatie.name: permit[PermitParams.zaakidentificatie.value],
            PermitParams.geldigVanaf.name: self._parse_datum_tot(permit["fields"][PermitParams.geldigVanaf.value]),
            PermitParams.geldigTot.name: self._parse_datum_tot(permit["fields"][PermitParams.geldigTot.value]),
        }

    def _parse_permit(self, permit: dict) -> dict:
        fields = permit["fields"]
        data = {
            PermitParams.zaakidentificatie.name: permit[PermitParams.zaakidentificatie.value],
            PermitParams.ontheffingsnummer.name: str(int(float(fields[PermitParams.ontheffingsnummer.value]))),
            PermitParams.geldigVanaf.name: self._parse_datum_vanaf(fields[PermitParams.geldigVanaf.value]),
            PermitParams.geldigTot.name: self._parse_datum_tot(fields[PermitParams.geldigTot.value]),
        }
        return data

    def _build_url(self, *, zaaknummer: str, folder: str) -> str:
        return os.path.join(self.base_url, zaaknummer, folder)

    def _parse_datum_vanaf(self, date_string: str) -> str:
        dt = datetime.fromisoformat(date_string)
        return dt.strftime('%Y-%m-%d')

    def _parse_datum_tot(self, date_string: str) -> str:
        """ De datum velden van Decos zijn 'tot en met'. Cleopatra verwacht velden als 'tot' """
        dt = datetime.fromisoformat(date_string) + timedelta(days=1)
        return dt.strftime('%Y-%m-%d')


class DecosTaxiDriver(DecosTaxi):
    def get_ontheffingen(self, *, driver_bsn: str, ontheffingsnummer: str) -> list[dict]:
        """
        request the permit from a driver based on their bsn nr
        """
        driver_data = self._get_driver_decos_key(driver_bsn)
        if not driver_data.get("content"):
            return []
        driver_key = self._parse_driver_key(driver_data)
        permits_data = self._get_ontheffing(driver_key=driver_key, ontheffingsnummer=ontheffingsnummer)
        driver_permits = self._parse_decos_permits(permits_data, ontheffingsnummer=ontheffingsnummer)
        for permit in driver_permits:
            self._add_enforcement_cases_to_permit_data(permit)
        return driver_permits

    def _get_driver_decos_key(self, driver_bsn: str) -> dict:
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
        return data

    def _parse_driver_key(self, data: dict) -> str:
        try:
            return data["content"][0]["key"]
        except:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the response from Decos")

    def _get_ontheffing(self, *, driver_key: str, ontheffingsnummer: str):
        class DecosParams(Enum):
            geldigVanaf = "date6"
            geldigTot = "date7"
            afgehandeld = "processed"
            resultaat = "dfunction"
            zaaktype = "text45"
            ontheffingsnummer = "it_sequence"

        odata_filter = OdataFilterParser()
        filters = [
            {"_eq": {DecosParams.zaaktype.value: "TAXXXI Zone-ontheffing"}},
            {"_eq": {DecosParams.afgehandeld.value: "true"}},
            {"_eq": {DecosParams.ontheffingsnummer.value: ontheffingsnummer}},
        ]
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        # Het zaaknummer refereerd in deze URL naar de chauffeur!
        url = self._build_url(zaaknummer=driver_key, folder=DecosFolders.folders.value)
        data = self._get(url, parameters)
        return data

    def _parse_decos_permits(self, data: dict, ontheffingsnummer: str) -> list[dict]:
        try:
            parsed_permits = []
            for permit in data["content"]:
                permit["fields"].update({PermitParams.ontheffingsnummer.value: ontheffingsnummer})
                parsed_permits.append(self._parse_permit(permit))
            return parsed_permits
        except KeyError as e:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the ontheffing from Decos") from e


class DecosTaxiDetail(DecosTaxi):
    def get_ontheffingen(self, ontheffingsnummer: str) -> list[dict]:
        data = self._get_ontheffing(ontheffingsnummer)
        if not data.get("content"):
            raise HTTPExceptions.NOT_FOUND.with_content("No data found in Decos for that query")
        detail_permits = self._parse_decos_permits(data)
        permit = detail_permits[0]
        self._add_enforcement_cases_to_permit_data(permit)
        return permit

    def _get_ontheffing(self, ontheffingsnummer: str):
        class DecosParams(Enum):
            geldigVanaf = "date6"
            geldigTot = "date7"
            afgehandeld = "processed"
            resultaat = "dfunction"
            zaaktype = "text45"
            ontheffingsnummer = "it_sequence"

        odata_select = OdataSelectParser()
        odata_filter = OdataFilterParser()
        filters = [
            {"_eq": {DecosParams.afgehandeld.value: "true"}},
            {"_eq": {DecosParams.ontheffingsnummer.value: ontheffingsnummer}},
        ]
        parameters = {
            "properties": "false",
            "fetchParents": "false",
            "oDataQuery.filter": odata_filter.parse(filters),
        }
        url = self._build_url(
            zaaknummer=DecosZaaknummers.zone_ontheffing.value,
            folder=DecosFolders.folders.value,
        )
        data = self._get(url, parameters)
        return data

    def _parse_decos_permits(self, data: dict) -> list[dict]:
        try:
            parsed_permits = [
                self._parse_permit(permit)
                for permit in data["content"]
            ]
            return parsed_permits
        except KeyError as e:
            raise HTTPExceptions.NOT_IMPLEMENTED.with_content("Could not parse the ontheffing from Decos") from e
