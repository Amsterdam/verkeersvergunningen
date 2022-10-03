from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from tests.utils import MockResponse
from .mock_data import mock_handhavingszaken
from taxi.decos import PermitParams


@pytest.fixture
def client():
    return APIClient()


def force_auth(*args, **kwargs):
    return "user", None


@patch("main.authentication.BasicAuthWithKeys.authenticate", force_auth)
class TestUrls:
    @patch("taxi.decos.DecosTaxi._get_driver_decos_key", lambda *args, **kwargs: "bsn_fake_1234567")
    @patch(
        "taxi.decos.DecosTaxi._get_ontheffingen",
        lambda *args, **kwargs: [
            {
                PermitParams.zaakidentificatie.name: "permit_fake_12345",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            }
        ],
    )
    @patch(
        "taxi.decos.DecosTaxi._get_handhavingzaken",
        lambda *args, **kwargs: [
            {
                PermitParams.zaakidentificatie.name: "schorsing_fake_12345",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            }
        ],
    )
    def test_ontheffingen_bsn(self, client):
        data = {"bsn": 12345678}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.zaakidentificatie.name] == "permit_fake_12345"
        assert (
            response.data["ontheffing"][0]["schorsingen"][0][PermitParams.zaakidentificatie.name]
            == "schorsing_fake_12345"
        )

    @patch(
        "taxi.decos.DecosTaxi._get_ontheffingen",
        lambda *args, **kwargs: [
            {
                PermitParams.zaakidentificatie.name: "permit_fake_12345",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            }
        ],
    )
    @patch(
        "taxi.decos.DecosTaxi._get_handhavingzaken",
        lambda *args, **kwargs: [
            {
                PermitParams.zaakidentificatie.name: "schorsing_fake_12345",
                PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
                PermitParams.geldigTot.name: "2022-09-26T00:00:00",
            }
        ],
    )
    def test_ontheffingen_detail(self, client):
        kwargs = {"ontheffingsnummer": "123456ab"}
        url = reverse("taxi_ontheffing_details", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data
        assert response.data[PermitParams.zaakidentificatie.name] == "permit_fake_12345"
        assert response.data["schorsingen"][0][PermitParams.zaakidentificatie.name] == "schorsing_fake_12345"

    @patch("taxi.decos.DecosTaxi._get_response", lambda *args, **kwargs: MockResponse(200, mock_handhavingszaken()))
    def test_get_ontheffing_detail_endpoint(self, client):
        kwargs = {"ontheffingsnummer": "123456ab"}
        url = reverse("taxi_ontheffing_details", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
