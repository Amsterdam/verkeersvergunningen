from requests import Request

import pytest

from unittest.mock import patch

import taxi
from taxi.serializers import OntheffingDetailSerializer, HandhavingSerializer
from .mock_data import *

from taxi.decos import DecosTaxi, DecosTaxiDetail, DecosTaxiDriver
from taxi.enums import DecosZaaknummers
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
            serializer = OntheffingDetailSerializer(data=permit)
            assert serializer.is_valid()

    def test_parse_decos_permits_driver(self, decos):
        mock_data = mock_ontheffing_driver()
        mock_data["content"][0]["fields"]["sequence"] = "ontheffingsnummer123"
        permits = decos._parse_decos_permits(mock_data)
        for permit in permits:
            permit["schorsingen"] = []
            serializer = OntheffingDetailSerializer(data=permit)
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
        mocked_response.side_effect = [
            MockResponse(200, mock_driver()),
            MockResponse(200, mock_ontheffing_driver()),
            MockResponse(200, mock_handhavingen()),
        ]
        driver_permits = decos.get_ontheffingen(driver_bsn=bsn, ontheffingsnummer=ontheffingsnummer)
        assert len(driver_permits) == 1
        assert len(driver_permits[0]["schorsingen"]) == 2

    @patch("taxi.decos.DecosTaxiDriver._get_response")
    def test_get_ontheffing_driver_empty(self, mocked_response, decos):
        mocked_response.side_effect = [
            MockResponse(200, mock_driver()),
            MockResponse(200, mock_ontheffing_driver_empty()),
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

    @patch(
        "taxi.decos.DecosTaxiDetail._get_response",
        lambda *args, **kwargs: MockResponse(200, content="Some string response"),
    )
    def test_string_response(self, decos_detail):
        with pytest.raises(HTTPExceptions.NOT_FOUND):
            decos_detail.get_ontheffingen(ontheffingsnummer="123")
