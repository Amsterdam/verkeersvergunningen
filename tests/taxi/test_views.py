from django.http import HttpResponse
from django.test import TestCase
import json
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIRequestFactory

from taxi.views import PermitView


class TestTaxiViews:

    @patch('main.authentication.BasicAuthWithKeys.authenticate',
           lambda *args, **kwargs: ('user', None))
    @patch('taxi.utils.DecosTaxi.get_decos_key',
           lambda *args, **kwargs: 'bsn_fake_1234567')
    @patch('taxi.utils.DecosTaxi.get_driver_permits',
           lambda *args, **kwargs: ['permit_fake_12345'])
    def test_post_permits_endpoint(self):
        factory = APIRequestFactory()
        view = PermitView.as_view()

        data = json.dumps({
            'bsn': '123456ab'
        })
        url = reverse("taxi_exemption")
        request = factory.post(content_type="application/json",
                               path=url, data=data,
                               HTTP_AUTHORIZATION='12345')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK