import json
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIRequestFactory

from taxi.views import OntheffingView, HandhavingView
from tests.utils import MockResponse


def force_auth(*args, **kwargs):
    return 'user', None


@patch('main.authentication.BasicAuthWithKeys.authenticate', force_auth)
class TestTaxiViews:
    @patch('taxi.utils.DecosTaxi.get_driver_decos_key',
           lambda *args, **kwargs: 'bsn_fake_1234567')
    @patch('taxi.utils.DecosTaxi.get_driver_ontheffing_en_handhaving',
           lambda *args, **kwargs: ['permit_fake_12345'])
    def test_post_ontheffing_endpoint(self):
        factory = APIRequestFactory()
        view = OntheffingView.as_view()

        data = json.dumps({
            'bsn': 123456
        })
        url = reverse("taxi_ontheffing")
        request = factory.post(content_type="application/json",
                               path=url, data=data)
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert 'vergunningsnummer' in response.data['ontheffing'][0]
        assert response.data['ontheffing'][0]['vergunningsnummer'] == 'permit_fake_12345'



    @patch('taxi.utils.DecosTaxi._get_response',
           lambda *args, **kwargs: MockResponse(200, {
                "count": 1,
                "content": [
                    {
                        "key": "7CAAF40DB75A46BDB5CD5B2A948221B3",
                        "fields": {},
                        "links": [
                            {
                                "rel": "self",
                                "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/items/7CAAF40DB75A46BDB5CD5B2A948221B3"
                            }
                        ]
                    }
                ],
                "links": [
                    {
                        "rel": "itemprofile",
                        "href": "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/itemprofiles/007992321A8F49E9AF5041EDF1504F20%7C2E617BAF63B34D3C9606F92E59C9E09F/list"
                    }
                ]
            }))
    def test_get_handhaving_endpoint(self):
        factory = APIRequestFactory()
        view = HandhavingView.as_view()

        kwargs = {
            'ontheffingsnummer': '123456ab'
        }
        url = reverse("taxi_handhaving", kwargs=kwargs)
        request = factory.get(path=url)
        response = view(request, ontheffingsnummer='12345ab')
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'content' in response.data
        assert 'links' in response.data

