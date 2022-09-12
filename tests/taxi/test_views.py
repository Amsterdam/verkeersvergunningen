from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIRequestFactory

from taxi.views import PermitView


class TestTaxiViews(TestCase):
    def setUp(self) -> None:
        pass

    @patch('taxi.utils.DecosTaxi.get_decos_key',
           lambda *args, **kwargs: 'bsn_fake_1234567')
    @patch('taxi.utils.DecosTaxi.get_driver_permits',
           lambda *args, **kwargs: ['permit_fake_12345'])
    def test_get_permits_endpoint(self):
        factory = APIRequestFactory()
        view = PermitView.as_view()

        kwargs = {
            'bsn': '123456'
        }
        url = reverse('taxi_permit', kwargs=kwargs)
        request = factory.post(content_type="application/json", path=url)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)