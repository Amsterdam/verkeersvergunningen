import pytest

from unittest import mock
from django.test import Client


@pytest.fixture
def http_client():
    return Client()


class TestViews:
    def test_health_view(self, http_client):
        response = http_client.get('/status/health')
        assert response.status_code == 200
        assert response.content == b"Connectivity OK"

    @mock.patch('health.views.settings.DEBUG', True)
    def test_debug_false(self, http_client):
        response = http_client.get('/status/health')
        assert response.status_code == 500
        assert response.content == b"Debug mode not allowed in production"
