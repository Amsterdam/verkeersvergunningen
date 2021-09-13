import base64
import json
from datetime import date, timedelta

import pytest
from django.conf import settings


class MockResponse:
    def __init__(self, status_code, json_content=None, content=None, headers=None):
        self.status_code = status_code
        self.json_content = json_content
        self.content = content
        self.headers = headers

    def json(self):
        return self.json_content


class TestVerkeersvergunningen:
    def setup(self):
        self.URL = '/zwaarverkeer/has_permit/'
        self.test_payload = {'number_plate': '1234AB', 'passage_at': '2022-01-01T13:00:00.000'}

        # Basic auth
        credentials = f"{settings.CLEOPATRA_BASIC_AUTH_USER}:{settings.CLEOPATRA_BASIC_AUTH_PASS}"
        auth_string = 'Basic ' + base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self.auth_headers = {'HTTP_AUTHORIZATION': auth_string}

    @pytest.mark.parametrize(
        'decos_count,expected_has_permit',
        [
            (0, False),
            (1, True),
            (2, True),
        ]
    )
    def test_basics(self, client, mocker, decos_count, expected_has_permit):
        mock_response = MockResponse(200, json_content={'count': decos_count})
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        response = client.post(
            self.URL,
            json.dumps(self.test_payload),
            content_type='application/json',
            **self.auth_headers
        )
        assert response.status_code == 200
        assert json.loads(response.content)['number_plate'] == self.test_payload['number_plate']
        assert json.loads(response.content)['has_permit'] == expected_has_permit
        # assert json.loads(response.content)['date_from'] == date.today().isoformat()
        # assert json.loads(response.content)['date_until'] == (date.today() + timedelta(days=1)).isoformat()

    def test_other_requests_than_post(self, client):
        response = client.get(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.put(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.patch(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.delete(self.URL, **self.auth_headers)
        assert response.status_code == 405

    def test_no_basic_auth_credentials_supplied_by_client(self, client, mocker):
        response = client.post(self.URL, json.dumps(self.test_payload), content_type='application/json')
        assert response.status_code == 401

    def test_wrong_basic_auth_credentials_supplied_by_client(self, client, mocker):
        response = client.post(
            self.URL,
            json.dumps(self.test_payload),
            content_type='application/json',
            HTTP_AUTHORIZATION='Basic wrong:wrong'
        )
        assert response.status_code == 401

    def test_wrong_basic_auth_credentials_for_decos(self, client, mocker):
        mock_response = MockResponse(401)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        response = client.post(
            self.URL,
            json.dumps(self.test_payload),
            content_type='application/json',
            **self.auth_headers
        )
        assert response.status_code == 502

    def test_invalid_json(self, client):
        response = client.post(
            self.URL,
            'invalid json',
            content_type='application/json',
            **self.auth_headers
        )
        assert response.status_code == 400

    def test_when_decos_is_not_available(self, client):
        # response = client.post(self.URL, json.dumps(self.test_payload), content_type='application/json')
        # assert response.status_code == 502
        pass
