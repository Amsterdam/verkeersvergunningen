from requests import Request

import pytest

from unittest.mock import patch

import taxi
from taxi.serializers import OntheffingDetailResponseSerializer, HandhavingSerializer
from .mock_data import *

from taxi.decos import DecosTaxi, DecosTaxiDetail, DecosTaxiDriver
from taxi.enums import DecosZaaknummers, PermitParams
from ..utils import MockResponse
from django_http_exceptions import HTTPExceptions

BASE_URL = DecosTaxi.base_url


@pytest.fixture
def decos():
    return DecosTaxiDriver()


@pytest.fixture
def decos_detail():
    return DecosTaxiDetail()


class TestDecosTaxiParse:
    def test_build_url(self, decos):
        zaaknr = "12345"
        endpoint = "my-endpoint"
        expected_url = f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/" f"api/v1/items/{zaaknr}/{endpoint}"
        response = decos._build_url(zaaknummer=zaaknr, folder=endpoint)
        assert expected_url == response

    def test_parse_driver_key(self, decos):
        data = mock_driver()
        decos_key = decos._parse_driver_key(data)
        assert decos_key == "07DAD65792F24AFEB59FF9D7028A6DD6"

    @pytest.mark.parametrize(
        "mock_data",
        [
            mock_ontheffing_driver_empty(),
            mock_ontheffing_detail(),
            mock_ontheffing_detail_empty(),
        ],
    )
    def test_parse_decos_permits(self, decos, mock_data):
        permits = decos._parse_decos_permits(mock_data)
        for permit in permits:
            permit["schorsingen"] = []
            serializer = OntheffingDetailResponseSerializer(data=permit)
            assert serializer.is_valid()

    def test_parse_decos_permits_driver(self, decos):
        mock_data = mock_ontheffing_driver()
        mock_data["content"][0]["fields"]["sequence"] = "ontheffingsnummer123"
        permits = decos._parse_decos_permits(mock_data)
        for permit in permits:
            permit["schorsingen"] = []
            serializer = OntheffingDetailResponseSerializer(data=permit)
            assert serializer.is_valid()

    def test_parse_decos_enforcement_cases(self, decos):
        mock_data = mock_handhavingen()
        handhavingen = decos._parse_decos_enforcement_cases(mock_data)
        for hhvng in handhavingen:
            serializer = HandhavingSerializer(data=hhvng)
            assert serializer.is_valid()


class TestDecosTaxiRequests:
    def test_get_empty_response(self, decos, mocker):
        mock_response = MockResponse(200, json_content=mock_ontheffing_driver_empty())
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)
        with pytest.raises(HTTPExceptions.NO_CONTENT):
            decos._get_ontheffing(driver_key="123", ontheffingsnummer="123")

    def test_get_driver_decos_key_request(self, decos, mocker):
        mock_response = MockResponse(200, json_content=mock_driver())
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        bsn = "233090125"
        decos._get_driver_decos_key(driver_bsn=bsn)

        request_url = (
            BASE_URL + DecosZaaknummers.bsn.value + "/TAXXXI?properties=false&fetchParents=false&"
            "oDataQuery.select=num1&oDataQuery.filter=num1%20eq%20%27233090125%27"
        )
        self._assert_correct_url(request_url)

    def test_get_ontheffing_driver_request(self, decos, mocker):
        mock_response = MockResponse(200, json_content=mock_ontheffing_driver())
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        driver_key = "07DAD65792F24AFEB59FF9D7028A6DD6"
        ontheffingnr = "1978110"
        decos._get_ontheffing(driver_key=driver_key, ontheffingsnummer=ontheffingnr)

        request_url = (
            BASE_URL + driver_key + "/FOLDERS?properties=false&fetchParents=false&"
            "oDataQuery.select=date6%2Cdate7%2Cprocessed%2Cdfunction%2Ctext45%2Cit_sequence&"
            "oDataQuery.filter=text45%20eq%20%27TAXXXI%20Zone-ontheffing%27%20and%20"
            "processed%20eq%20%27true%27%20and%20it_sequence%20eq%20%271978110%27"
        )
        self._assert_correct_url(request_url)

    def test_get_ontheffing_detail_request(self, decos_detail, mocker):
        mock_response = MockResponse(200, json_content=mock_ontheffing_detail())
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        ontheffingnr = "1978110"
        decos_detail._get_ontheffing(ontheffingsnummer=ontheffingnr)

        # Check if the prepared url is correct
        request_url = (
            BASE_URL + DecosZaaknummers.zone_ontheffing.value + "/FOLDERS?properties=false&fetchParents=false&"
            "oDataQuery.select=date6%2Cdate7%2Cprocessed%2Cdfunction%2Ctext45%2Cit_sequence&"
            "oDataQuery.filter=processed%20eq%20%27true%27%20and%20it_sequence%20eq%20%271978110%27"
        )
        self._assert_correct_url(request_url)

    def test_get_handhaving_request(self, decos, mocker):
        mock_response = MockResponse(200, json_content=mock_handhavingen())
        mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)

        ontheffingsnr = "8E5F8EB000EC4938BC894CA2313E9134"
        decos._get_handhavingzaken(permit_decos_key=ontheffingsnr)

        request_url = (
            BASE_URL
            + DecosZaaknummers.handhavingszaken.value
            + f"/FOLDERS?properties=false&fetchParents=false&relTypeKey={ontheffingsnr}&"
            "oDataQuery.select=dfunction%2Cdate6%2Cdate7"
        )
        self._assert_correct_url(request_url)

    def _assert_correct_url(self, expected_request_url):
        mocked_response_function = taxi.decos.DecosTaxi._get_response
        call_args_kwargs = mocked_response_function.call_args.kwargs
        r = Request(**call_args_kwargs).prepare()
        assert r.url == expected_request_url


class TestDecosTaxiResponse:
    @patch("taxi.decos.DecosTaxiDriver._get_response")
    def test_get_ontheffing_driver(self, mocked_response, decos):
        ontheffingsnummer, bsn = "123", "123"
        driver_ontheffing = mock_ontheffing_driver()
        driver_ontheffing["content"][0]["fields"][PermitParams.ontheffingsnummer.value] = ontheffingsnummer

        mocked_response.side_effect = [
            MockResponse(200, mock_driver()),
            MockResponse(200, driver_ontheffing),
            MockResponse(200, mock_handhavingen()),
        ]
        driver_permits = decos.get_ontheffingen(driver_bsn=bsn, ontheffingsnummer=ontheffingsnummer)
        assert len(driver_permits) == 1
        assert len(driver_permits[0]["schorsingen"]) == 2

    @patch("taxi.decos.DecosTaxiDriver._get_response")
    def test_get_ontheffing_driver_empty(self, mocked_response, decos):
        mocked_response.side_effect = [
            MockResponse(200, mock_driver()),
            MockResponse(200, mock_ontheffing_driver_empty())
        ]
        with pytest.raises(HTTPExceptions.NO_CONTENT):
            decos.get_ontheffingen(driver_bsn="123", ontheffingsnummer="123")

    @patch("taxi.decos.DecosTaxiDetail._get_response")
    def test_get_ontheffing_detail(self, mocked_response, decos_detail):
        mocked_response.side_effect = [
            MockResponse(200, mock_ontheffing_detail()),
            MockResponse(200, mock_handhavingen()),
        ]
        driver_permits = decos_detail.get_ontheffingen(ontheffingsnummer="123")
        assert len(driver_permits) == 1
        assert len(driver_permits[0]["schorsingen"]) == 2

    @patch("taxi.decos.DecosTaxiDetail._get_response")
    def test_get_ontheffing_detail_empty(self, mocked_response, decos_detail):
        mocked_response.side_effect = [
            MockResponse(200, mock_ontheffing_detail_empty()),
            MockResponse(200, mock_handhavingen()),
        ]
        with pytest.raises(HTTPExceptions.NO_CONTENT):
            decos_detail.get_ontheffingen(ontheffingsnummer="123")

    #
    # @patch(
    #     "taxi.decos.DecosTaxi._get_response",
    #     lambda *args, **kwargs: MockResponse(
    #         200,
    #         mock_handhavingszaken(),
    #     ),
    # )
    # def test_get_handhavingzaken(self, decos):
    #     permit_decos_key = "fake_key_12395"
    #     enforcement_cases = decos._get_handhavingzaken(permit_decos_key=permit_decos_key)
    #     assert enforcement_cases == mock_parsed_enforcement_cases()
    #
    # @patch("taxi.decos.DecosTaxi._get_handhavingzaken", return_value=mock_parsed_enforcement_cases())
    # def test_add_enforcement_cases_to_permit_data(self, mock_get_handhavingszaken, decos):
    #     permit = {
    #         PermitParams.zaakidentificatie.name: "fake_permit_123",
    #         PermitParams.geldigVanaf.name: "2022-08-29",
    #         PermitParams.geldigTot.name: "2022-09-28",
    #     }
    #     permit_values = {**permit}
    #     decos._add_enforcement_cases_to_permit_data(permit=permit)
    #
    #     mock_get_handhavingszaken.assert_called_with(permit_decos_key="fake_permit_123")
    #     assert permit == {**permit_values, "schorsingen": mock_parsed_enforcement_cases()}
    #
    # @patch(
    #     "taxi.decos.DecosTaxi._get_response",
    #     lambda *args, **kwargs: MockResponse(
    #         200,
    #         {
    #             "content": [
    #                 {"key": "0987654", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #                 {"key": "12345678", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #             ]
    #         },
    #     ),
    # )
    # def test_get_ontheffingen_driver_simple(self, decos):
    #     driver_decos_key = "1234567"
    #     permits = decos._get_ontheffingen_driver(driver_decos_key)
    #     assert [p[PermitParams.zaakidentificatie.name] for p in permits] == ["0987654", "12345678"]
    #
    # def test_get_ontheffingen_driver_extensive(self, mocker, decos):
    #     DECOS_KEY = "07DAD65792F24AFEB59FF9D7028A6DD6"
    #     PERMIT_1 = "7CAAF40DB75A46BDB5CD5B2A948221B3"
    #     PERMIT_2 = "8E5F8EB000EC4938BC894CA2313E9134"
    #     expected_request_url = (
    #         f"https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/{DECOS_KEY}/FOLDERS"
    #         f"?properties=false&fetchParents=false"
    #         f"&oDataQuery.select=date6%2Cdate7%2Cprocessed%2Cdfunction%2Ctext45"
    #         f"&oDataQuery.filter=text45%20eq%20%27TAXXXI%20Zone-ontheffing%27%20"
    #         f"and%20processed%20eq%20%27true%27"
    #     )
    #     decos_response = {
    #         "content": [
    #             {"key": PERMIT_1, "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #             {"key": PERMIT_2, "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #         ]
    #     }
    #     mock_response = MockResponse(200, json_content=decos_response)
    #     mocker.patch("taxi.decos.DecosTaxi._get_response", return_value=mock_response)
    #
    #     permits = decos._get_ontheffingen_driver(driver_decos_key=DECOS_KEY)
    #
    #     # Check if the prepared url is correct
    #     mocked_response_function = taxi.decos.DecosTaxi._get_response
    #     call_args_kwargs = mocked_response_function.call_args.kwargs
    #     r = Request(**call_args_kwargs).prepare()
    #     assert r.url == expected_request_url
    #     # Check if the return value is parsed correctly
    #     assert [p[PermitParams.zaakidentificatie.name] for p in permits] == [PERMIT_1, PERMIT_2]
    #
    # @patch("taxi.decos.DecosTaxi._get_driver_decos_key", lambda *args, **kwargs: "fake_758697")
    # @patch(
    #     "taxi.decos.DecosTaxi._get_response",
    #     lambda *args, **kwargs: MockResponse(
    #         200,
    #         {
    #             "content": [
    #                 {"key": "abcd12346", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #                 {"key": "12345678abc", "fields": {"date6": "2022-08-29T00:00:00", "date7": "2022-09-28T00:00:00"}},
    #             ]
    #         },
    #     ),
    # )
    # def test_get_ontheffingen_by_driver_bsn(self, decos):
    #     bsn = "bsn_fake"
    #     driver_permits = decos.get_ontheffing(driver_bsn=bsn)
    #     assert [p[PermitParams.zaakidentificatie.name] for p in driver_permits] == ["abcd12346", "12345678abc"]
