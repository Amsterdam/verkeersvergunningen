from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from tests.utils import MockResponse
from .mock_data import mock_handhavingszaken


@pytest.fixture
def client():
    return APIClient()


def force_auth(*args, **kwargs):
    return "user", None


@patch("main.authentication.BasicAuthWithKeys.authenticate", force_auth)
class TestUrls:
    @patch("taxi.utils.DecosTaxi.get_driver_decos_key", lambda *args, **kwargs: "bsn_fake_1234567")
    @patch("taxi.utils.DecosTaxi.get_driver_ontheffing_en_handhaving", lambda *args, **kwargs: ["permit_fake_12345"])
    def test_ontheffingen(self, client):
        data = {"bsn": 12345678}
        url = reverse("taxi_ontheffing")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert "vergunningsnummer" in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0]["vergunningsnummer"] == "permit_fake_12345"

    @patch("taxi.utils.DecosTaxi._get_response", lambda *args, **kwargs: MockResponse(200, mock_handhavingszaken()))
    def test_get_handhaving_endpoint(self, client):
        kwargs = {"ontheffingsnummer": "123456ab"}
        url = reverse("taxi_handhaving", kwargs=kwargs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "content" in response.data
        assert "links" in response.data