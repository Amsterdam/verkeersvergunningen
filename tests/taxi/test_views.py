from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from taxi.enums import PermitParams
from .mock_data import *


@pytest.fixture
def client():
    return APIClient()


def force_auth(*args, **kwargs):
    return "user", None


@patch("main.authentication.BasicAuthWithKeys.authenticate", force_auth)
class TestUrls:
    @patch("taxi.decos.DecosTaxiDriver._get_driver_decos_key", mock_driver())
    @patch("taxi.decos.DecosTaxiDriver._get_ontheffing", mock_ontheffing_driver())
    @patch("taxi.decos.DecosTaxiDriver._get_handhavingzaken", mock_handhavingen())
    def test_ontheffingen_bsn(self, client):
        data = {"bsn": 123456789, "ontheffingsnummer": 1234567}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.zaakidentificatie.name] == "8E5F8EB000EC4938BC894CA2313E9134"
        assert (
            response.data["ontheffing"][0]["schorsingen"][0][PermitParams.zaakidentificatie.name]
            == "8E5F8EB000EC4938BC894CA2313E9134"
        )

    def test_ontheffingen_bsn_too_few_digits(self, client):
        data = {"bsn": 123, "ontheffingsnummer": 1234567}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_ontheffingen_bsn_ontheffingsnummer_too_many_digits(self, client):
        data = {"bsn": 123456789, "ontheffingsnummer": 1234567890}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch(
        "taxi.decos.DecosTaxiDriver.get_ontheffingen",
        lambda *args, **kwargs: [
            {
                "zaakidentificatie": "8E5F8EB000EC4938BC894CA2313E9134",
                "geldigVanaf": "2022-08-01T00:00:00",
                "geldigTot": "2025-07-31T00:00:00",
                "schorsingen": [
                    {
                        "ontheffingsnummer": "1234567",
                        "geldigVanaf": "2022-08-29T00:00:00",
                        "geldigTot": "2022-09-28T00:00:00",
                    },
                    {
                        "ontheffingsnummer": "1234567",
                        "geldigVanaf": "2022-09-05T00:00:00",
                        "geldigTot": "2022-09-26T00:00:00",
                    },
                ],
            }
        ],
    )
    def test_get_ontheffingen_by_driver_bsn(self, client):
        data = {"bsn": 123456789, "ontheffingsnummer": 1234567}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.zaakidentificatie.name] == "8E5F8EB000EC4938BC894CA2313E9134"
        assert len(response.data["ontheffing"][0]["schorsingen"]) == 2

    @patch("taxi.decos.DecosTaxiDetail._get_ontheffing", mock_ontheffing_detail())
    @patch("taxi.decos.DecosTaxiDetail._get_handhavingzaken", mock_handhavingen())
    def test_ontheffingen_detail(self, client):
        kwargs = {"ontheffingsnummer": 1234567}
        url = reverse("taxi_ontheffing_details", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data
        assert response.data[PermitParams.zaakidentificatie.name] == "permit_fake_12345"
        assert response.data["schorsingen"][0][PermitParams.zaakidentificatie.name] == "schorsing_fake_12345"
