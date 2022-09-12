import pytest

from unittest.mock import patch
from main.utils import ImmediateHttpResponse
from .mock_data import mock_zaaknummer
from django.test import TestCase, SimpleTestCase

from taxi.utils import DecosTaxi
from ..utils import MockResponse


class TestDecosTaxi(SimpleTestCase):

    def setUp(self) -> None:
        self.decos = DecosTaxi()

    def test_build_url(self):
        zaaknr = '12345'
        endpoint = 'my-endpoint'
        expected_url = f'https://decosdvl.acc.amsterdam.nl/decosweb/aspx/' \
                       f'api/v1/items/{zaaknr}/{endpoint}'
        response = self.decos._build_url(zaaknummer=zaaknr,
                                         endpoint=endpoint)
        self.assertEqual(expected_url, response)

    def test_parse_zaaknummer(self):
        zaaknr = '555aaa555'
        data = mock_zaaknummer()
        response = self.decos._parse_zaaknummers(data)
        self.assertEqual([zaaknr], response)

    def test_invalid_parse_zaaknummer(self):
        data = {'invalid': 'data'}
        with pytest.raises(ImmediateHttpResponse):
            self.decos._parse_zaaknummers(data)

    @patch('taxi.utils.DecosTaxi._get_response',
           lambda *args, **kwargs: MockResponse(200, {
               'content': [
                   {'key': '0987654'}
               ]
           }))
    def test_get_decos_key(self):
        bsn_nr = 'fake_number'
        key = self.decos.get_decos_key(bsn_nr)
        self.assertEqual('0987654', key)

    @patch('taxi.utils.DecosTaxi._get_response',
           lambda *args, **kwargs: MockResponse(200, {
               'content': [
                   {'key': '0987654', 'some_other': 'data'},
                   {'key': '12345678'}
               ]
           }))
    def test_get_driver_permits(self):
        driver_decos_key = '1234567'
        permits = self.decos.get_driver_permits(driver_decos_key)
        self.assertEqual(['0987654', '12345678'], permits)

    @patch('taxi.utils.DecosTaxi._get_response',
           lambda *args, **kwargs: MockResponse(200, {
               'content': [
                   {'key': '0987654', 'some_other': 'data'},
                   {'key': '12345678'}
               ]
           }))
    def test_get_enforcement_cases(self):
        license_casenr = 'fake'
        cases = self.decos.get_enforcement_cases(license_casenr)
        self.assertEqual(['0987654', '12345678'], cases)

    @patch('taxi.utils.DecosTaxi._get_response',
           lambda *args, **kwargs: MockResponse(200, {
               'content': [
                   {'key': 'abcd12346', 'some_other': 'data'},
                   {'key': '12345678abc'}
               ]
           }))
    def test_get_taxi_permit(self):
        bsn = 'bsn_fake'
        driver_permits = self.decos.get_taxi_permit(bsn)
        self.assertEqual(['abcd12346', '12345678abc'], driver_permits)
