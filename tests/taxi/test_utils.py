from requests import Request

import pytest

from unittest.mock import patch

import taxi
from main.utils import ImmediateHttpResponse
from .mock_data import mock_zaaknummer

from taxi.utils import DecosTaxi
from ..utils import MockResponse


@pytest.fixture
def decos():
    return DecosTaxi()


class TestDecosTaxi:
    def test_build_url(self, decos):
        zaaknr = "12345"
        endpoint = "my-endpoint"
        expected_url = (
            f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/"
            f"api/v1/items/{zaaknr}/{endpoint}"
        )
        response = decos._build_url(zaaknummer=zaaknr, endpoint=endpoint)
        assert expected_url == response

    def test_parse_key(self, decos):
        zaaknr = "555aaa555"
        data = mock_zaaknummer()
        response = decos._parse_key(data)
        assert [zaaknr] == response

    def test_invalid_parse_zaaknummer(self, decos):
        data = {"invalid": "data"}
        with pytest.raises(ImmediateHttpResponse):
            decos._parse_key(data)

    def test_get_decos_key(self, mocker, decos):
        DECOS_KEY = DecosTaxi.ZAAKNUMMER["BSN"]
        BSN_NUM = "233090125"
        expected_request_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/TAXXXI" \
                               f"?properties=false&fetchParents=false" \
                               f"&oDataQuery.select=NUM1&oDataQuery.filter=NUM1%20eq%20%27{BSN_NUM}%27"
        decos_response = {
            "content": [{"key": DECOS_KEY, "fields": {"num1": int(BSN_NUM)}}]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch("taxi.utils.DecosTaxi._get_response", return_value=mock_response)

        # Run code
        decos_key = decos.get_decos_key(driver_bsn=BSN_NUM)

        # Check if the prepared url is correct
        mocked_response_function = taxi.utils.DecosTaxi._get_response
        call_args_kwargs = mocked_response_function.call_args.kwargs
        r = Request(**call_args_kwargs).prepare()
        assert r.url == expected_request_url
        # Check if the return value is parsed correctly
        assert decos_key == DECOS_KEY

    @patch(
        "taxi.utils.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "0987654", "some_other": "data"},
                    {"key": "12345678"},
                ]
            },
        ),
    )
    def test_get_driver_permits_simple(self, decos):
        driver_decos_key = "1234567"
        permits = decos.get_driver_permits(driver_decos_key)
        assert ["0987654", "12345678"] == permits

    def test_get_driver_permits_extensive(self, mocker, decos):
        DECOS_KEY = "07DAD65792F24AFEB59FF9D7028A6DD6"
        PERMIT_1 = "7CAAF40DB75A46BDB5CD5B2A948221B3"
        PERMIT_2 = "8E5F8EB000EC4938BC894CA2313E9134"
        expected_request_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/FOLDERS" \
                               f"?properties=false&fetchParents=false" \
                               f"&oDataQuery.select=DATE6%2CDATE7%2CPROCESSED%2CDFUNCTION%2CTEXT45" \
                               f"&oDataQuery.filter=%28TEXT45%20eq%20%27TAXXXI%20Zone-ontheffing%27%20" \
                               f"or%20TEXT45%20eq%20%27TAXXXI%20Handhaving%27%29"
        decos_response = {
            "content": [
                {"key": PERMIT_1},
                {"key": PERMIT_2},
            ]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch("taxi.utils.DecosTaxi._get_response", return_value=mock_response)

        permits = decos.get_driver_permits(driver_decos_key=DECOS_KEY)

        # Check if the prepared url is correct
        mocked_response_function = taxi.utils.DecosTaxi._get_response
        call_args_kwargs = mocked_response_function.call_args.kwargs
        r = Request(**call_args_kwargs).prepare()
        assert r.url == expected_request_url
        # Check if the return value is parsed correctly
        assert permits == [PERMIT_1, PERMIT_2]

    @patch(
        "taxi.utils.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "0987654", "some_other": "data"},
                    {"key": "12345678"},
                ]
            },
        ),
    )
    def test_get_enforcement_cases(self, decos):
        license_casenr = "fake"
        cases = decos.get_enforcement_cases(license_casenr)
        assert ["0987654", "12345678"] == cases

    @patch("taxi.utils.DecosTaxi.get_decos_key", lambda *args, **kwargs: "fake_758697")
    @patch(
        "taxi.utils.DecosTaxi._get_response",
        lambda *args, **kwargs: MockResponse(
            200,
            {
                "content": [
                    {"key": "abcd12346", "some_other": "data"},
                    {"key": "12345678abc"},
                ]
            },
        ),
    )
    def test_get_taxi_permit(self, decos):
        bsn = "bsn_fake"
        driver_permits = decos.get_taxi_permit(bsn)
        assert ["abcd12346", "12345678abc"] == driver_permits
