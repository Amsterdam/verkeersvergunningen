from requests import Request

import pytest

from unittest.mock import patch

import taxi
from main.exceptions import ImmediateHttpResponse
from .mock_data import mock_zaaknummer, mock_permits

from taxi.decos import DecosTaxi
from taxi.enums import DecosZaaknummers, PermitParams
from ..utils import MockResponse


@pytest.fixture
def decos():
    return DecosTaxi()


class TestDecosTaxi:
    def test_build_url(self, decos):
        zaaknr = "12345"
        endpoint = "my-endpoint"
        expected_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/" f"api/v1/items/{zaaknr}/{endpoint}"
        response = decos._build_url(zaaknummer=zaaknr, folder=endpoint)
        assert expected_url == response

    def test_parse_decos_key(self, decos):
        zaaknr = "555aaa555"
        data = mock_zaaknummer()
        response = decos._parse_decos_key(data)
        assert [zaaknr] == response

    def test_parse_decos_permits(self, decos):
        permits = [
            {
                PermitParams.zaakidentificatie.name: "7CAAF40DB75A46BDB5CD5B2A948221B3",
                PermitParams.geldigVanaf.name: "2022-08-29T00:00:00",
                PermitParams.geldigTot.name: "2022-09-28T00:00:00",
            },
            {
                PermitParams.zaakidentificatie.name: "C06C49DC3BAA48E7A38C0D11F97D9770",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            },
        ]
        data = mock_permits()
        response = decos._parse_decos_permits(data)
        assert response == permits

    def test_invalid_parse_zaaknummer(self, decos):
        data = {"invalid": "data"}
        with pytest.raises(ImmediateHttpResponse):
            decos._parse_decos_key(data)

    def test_get_decos_key(self, mocker, decos):

        DECOS_KEY = DecosZaaknummers.bsn.value
        BSN_NUM = "233090125"
        expected_request_url = (
            f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/TAXXXI"
            f"?properties=false&fetchParents=false"
            f"&oDataQuery.select=num1&oDataQuery.filter=num1%20eq%20%27{BSN_NUM}%27"
        )
        decos_response = {"content": [{"key": DECOS_KEY, "fields": {"num1": int(BSN_NUM)}}]}
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        # Run code
        decos_key = decos._get_driver_decos_key(driver_bsn=BSN_NUM)

        # Check if the prepared url is correct
        mocked_response_function = taxi.decos.DecosTaxi._get_response
        call_args_kwargs = mocked_response_function.call_args.kwargs
        r = Request(**call_args_kwargs).prepare()
        assert r.url == expected_request_url
        # Check if the return value is parsed correctly
        assert decos_key == DECOS_KEY

    @patch(
        "taxi.decos.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "0987654", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                    {"key": "12345678", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                ]
            },
        ),
    )
    def test_get_driver_permits_simple(self, decos):
        driver_decos_key = "1234567"
        permits = decos._get_ontheffingen(driver_decos_key)
        assert [p[PermitParams.zaakidentificatie.name] for p in permits] == ["0987654", "12345678"]

    def test_get_driver_permits_extensive(self, mocker, decos):
        DECOS_KEY = "07DAD65792F24AFEB59FF9D7028A6DD6"
        PERMIT_1 = "7CAAF40DB75A46BDB5CD5B2A948221B3"
        PERMIT_2 = "8E5F8EB000EC4938BC894CA2313E9134"
        expected_request_url = (
            f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/FOLDERS"
            f"?properties=false&fetchParents=false"
            f"&oDataQuery.select=date6%2Cdate7%2Cprocessed%2Cdfunction%2Ctext45"
            f"&oDataQuery.filter=text45%20eq%20%27TAXXXI%20Zone-ontheffing%27%20"
            f"and%20processed%20eq%20%27true%27"
        )
        decos_response = {
            "content": [
                {"key": PERMIT_1, "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                {"key": PERMIT_2, "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
            ]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        url = decos._build_url(zaaknummer=DECOS_KEY, folder='FOLDERS')
        permits = decos._get_ontheffingen(url=url)

        # Check if the prepared url is correct
        mocked_response_function = taxi.decos.DecosTaxi._get_response
        call_args_kwargs = mocked_response_function.call_args.kwargs
        r = Request(**call_args_kwargs).prepare()
        assert r.url == expected_request_url
        # Check if the return value is parsed correctly
        assert [p[PermitParams.zaakidentificatie.name] for p in permits] == [PERMIT_1, PERMIT_2]

    @patch(
        "taxi.decos.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "0987654", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                    {"key": "12345678", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                ]
            },
        ),
    )
    def test_get_enforcement_cases(self, decos):
        license_casenr = "fake"
        cases = decos._get_handhavingzaken(license_casenr)
        assert [p[PermitParams.zaakidentificatie.name] for p in cases] == ["0987654", "12345678"]

    @patch("taxi.decos.DecosTaxi._get_driver_decos_key", lambda *args, **kwargs: "fake_758697")
    @patch(
        "taxi.decos.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "abcd12346", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                    {"key": "12345678abc", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
                ]
            },
        ),
    )
    def test_get_taxi_permit(self, decos):
        bsn = "bsn_fake"
        driver_permits = decos.get_ontheffingen_by_driver_bsn(driver_bsn=bsn)
        assert [p[PermitParams.zaakidentificatie.name] for p in driver_permits] == ["abcd12346", "12345678abc"]
