from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from taxi.enums import PermitParams
from .mock_data import *
from ..utils import MockResponse


@pytest.fixture
def client():
    return APIClient()


def force_auth(*args, **kwargs):
    return "user", None


@patch("main.authentication.BasicAuthWithKeys.authenticate", force_auth)
class TestViews:
    @patch("taxi.decos.DecosTaxiDriver._get_driver_decos_key", lambda *args, **kwargs: mock_driver())
    @patch("taxi.decos.DecosTaxiDriver._get_ontheffing", lambda *args, **kwargs: mock_ontheffing_driver())
    @patch("taxi.decos.DecosTaxiDriver._get_handhavingzaken", lambda *args, **kwargs: mock_handhavingen())
    def test_ontheffingen_bsn(self, client):
        data = {"bsn": '123456789', "ontheffingsnummer": '1234567'}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.ontheffingsnummer.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.ontheffingsnummer.name] == str(data["ontheffingsnummer"])
        assert (
            response.data["ontheffing"][0]["schorsingen"][0][PermitParams.zaakidentificatie.name]
            == "7CAAF40DB75A46BDB5CD5B2A948221B3"
        )

    def test_ontheffingen_bsn_too_few_digits(self, client):
        data = {"bsn": '123', "ontheffingsnummer": '1234567'}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ontheffingen_bsn_ontheffingsnummer_too_many_digits(self, client):
        data = {"bsn": '123456789', "ontheffingsnummer": '1234567890'}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert status.HTTP_400_BAD_REQUEST == response.status_code

    @patch(
        "taxi.decos.DecosTaxiDriver.get_ontheffingen",
        lambda *args, **kwargs: [
            {
                "ontheffingsnummer": "8E5F8EB000EC4938BC894CA2313E9134",
                "geldigVanaf": "2022-08-01",
                "geldigTot": "2025-07-31",
                "schorsingen": [
                    {
                        "zaakidentificatie": "1234567",
                        "geldigVanaf": "2022-08-29",
                        "geldigTot": "2022-09-28",
                    },
                    {
                        "zaakidentificatie": "1234567",
                        "geldigVanaf": "2022-09-05",
                        "geldigTot": "2022-09-26",
                    },
                ],
            }
        ],
    )
    def test_get_ontheffingen_by_driver_bsn(self, client):
        data = {"bsn": '123456789', "ontheffingsnummer": '1234567'}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.ontheffingsnummer.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.ontheffingsnummer.name] == "8E5F8EB000EC4938BC894CA2313E9134"
        assert len(response.data["ontheffing"][0]["schorsingen"]) == 2

    @patch("taxi.decos.DecosTaxiDetail._get_ontheffing", lambda *args, **kwargs: mock_ontheffing_detail())
    @patch("taxi.decos.DecosTaxiDetail._get_handhavingzaken", lambda *args, **kwargs: mock_handhavingen())
    def test_ontheffingen_detail(self, client):
        kwargs = {"ontheffingsnummer": '1978110'}
        url = reverse("taxi_ontheffing_details", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.ontheffingsnummer.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.ontheffingsnummer.name] == str(kwargs["ontheffingsnummer"])
        assert (
            response.data["ontheffing"][0]["schorsingen"][0][PermitParams.zaakidentificatie.name]
            == "7CAAF40DB75A46BDB5CD5B2A948221B3"
        )

    @patch(
        "taxi.decos.DecosTaxiDetail._get_response",
        lambda *args, **kwargs: MockResponse(200, content="Some string response"),
    )
    def test_ontheffingen_detail_not_found(self, client):
        kwargs = {"ontheffingsnummer": '1978110'}
        url = reverse("taxi_ontheffing_details", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
