from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import pytest
from taxi.enums import PermitParams


@pytest.fixture
def client():
    return APIClient()


def force_auth(*args, **kwargs):
    return "user", None


@patch("main.authentication.BasicAuthWithKeys.authenticate", force_auth)
class TestUrls:
    @patch("taxi.decos.DecosTaxi._get_driver_decos_key", lambda *args, **kwargs: "bsn_fake_1234567")
    @patch(
        "taxi.decos.DecosTaxi._get_ontheffingen_driver",
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
        data = {"bsn": 123456789}
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
        "taxi.decos.DecosTaxi.get_ontheffingen_by_driver_bsn",
        lambda *args, **kwargs: [
            {
                "zaakidentificatie": "8E5F8EB000EC4938BC894CA2313E9134",
                "geldigVanaf": "2022-08-01T00:00:00",
                "geldigTot": "2025-07-31T00:00:00",
                "schorsingen": [
                    {
                        "zaakidentificatie": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                        "geldigVanaf": "2022-08-29T00:00:00",
                        "geldigTot": "2022-09-28T00:00:00",
                    },
                    {
                        "zaakidentificatie": "C06C49DC3BAA48E7A38C0D11F97D9770",
                        "geldigVanaf": "2022-09-05T00:00:00",
                        "geldigTot": "2022-09-26T00:00:00",
                    },
                ],
            }
        ],
    )
    def test_get_ontheffingen_by_driver_bsn(self, client):
        data = {"bsn": 123456789}
        url = reverse("taxi_ontheffingen_bsn")
        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert PermitParams.zaakidentificatie.name in response.data["ontheffing"][0]
        assert response.data["ontheffing"][0][PermitParams.zaakidentificatie.name] == "8E5F8EB000EC4938BC894CA2313E9134"
        assert len(response.data["ontheffing"][0]["schorsingen"]) == 2

    @patch(
        "taxi.decos.DecosTaxi._get_ontheffing_details",
        lambda *args, **kwargs: {
            PermitParams.zaakidentificatie.name: "permit_fake_12345",
            PermitParams.geldigVanaf.name: "2022-09-05T00:00:00",
            PermitParams.geldigTot.name: "2022-09-26T00:00:00",
        },
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
