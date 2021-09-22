import base64
import json

import pytest
from dateutil.parser import parse
from django.conf import settings

from zwaarverkeer.decos_join import DecosJoin


class MockResponse:
    def __init__(self, status_code, json_content=None, content=None, headers=None):
        self.status_code = status_code
        self.json_content = json_content
        self.content = content
        self.headers = headers

    def json(self):
        return self.json_content


def create_basic_auth_headers(username, password):
    credentials = f"{username}:{password}"
    auth_string = 'Basic ' + base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return {'HTTP_AUTHORIZATION': auth_string}


class TestDecosJoin:
    def setup(self):
        pass

    @pytest.mark.parametrize(
        'passage_at, permit_type, valid_from, valid_until, expected_valid_from, expected_valid_until',
        [
            # Year permit
            (
                '2021-10-10T06:30:00.000',
                'Jaarontheffing gewicht en ondeelbaar',
                '2021-09-10T00:00:00.000',
                '2022-09-10T00:00:00.000',
                '2021-09-10T00:00:00.000+2',
                '2022-09-11T00:00:00.000+2',
            ),

            # day permit today, passage before 6
            (
                '2021-10-10T05:30:00.000',
                'Dagontheffing',
                '2021-10-10T00:00:00.000',
                '2021-10-10T00:00:00.000',
                '2021-10-10T00:00:00.000+2',
                '2021-10-11T06:00:00.000+2',
            ),

            # day permit today, passage after 6
            (
                '2021-10-10T06:30:00.000',
                'Dagontheffing',
                '2021-10-10T00:00:00.000',
                '2021-10-10T00:00:00.000',
                '2021-10-10T00:00:00.000+2',
                '2021-10-11T06:00:00.000+2',
            ),

            # day permit yesterday, passage before 6
            (
                '2021-10-10T05:30:00.000',
                'Dagontheffing',
                '2021-10-09T00:00:00.000',
                '2021-10-09T00:00:00.000',
                '2021-10-09T00:00:00.000+2',
                '2021-10-10T06:00:00.000+2',
            ),

            # day permit yesterday, passage after 6
            # this means the permit is not valid for this passing, so we return None
            (
                    '2021-10-10T06:30:00.000',
                    'Dagontheffing',
                    '2021-10-09T00:00:00.000',
                    '2021-10-09T00:00:00.000',
                    None,
                    None
            ),

            # route permit today
            (
                '2021-10-10T06:30:00.000',
                'Routeontheffing gewicht en ondeelbaar',
                '2021-10-10T00:00:00.000',
                '2022-10-10T00:00:00.000',
                '2021-10-10T00:00:00.000+2',
                '2022-10-11T00:00:00.000+2',
            ),
        ],
    )
    def test_get_permits_with_a_single_permit(self, mocker, passage_at, permit_type, valid_from, valid_until, expected_valid_from, expected_valid_until):
        decos_response = {
            'count': 1,
            'content': [
                {
                    'fields': {
                        'text17': permit_type,
                        'subject1': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                        'date6': valid_from,
                        'date7': valid_until,
                    }
                }
            ]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        decos = DecosJoin()
        result = decos.get_permits('ABC123', parse(passage_at))
        expected = []
        if expected_valid_from:
            expected.append({
                'permit_type': permit_type,
                'permit_description': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                'valid_from': parse(expected_valid_from),
                'valid_until': parse(expected_valid_until),
            })
        assert result == expected



    @pytest.mark.parametrize(
        'passage_at, permits',
        [
            # Passage before 6 - both day permit (valid today) and a year permit
            (
                '2021-10-10T05:30:00.000',
                [
                    {
                        'permit_type': 'Dagontheffing',
                        'valid_from': '2021-10-10T00:00:00.000',
                        'valid_until': '2021-10-10T00:00:00.000',
                        'expected_valid_from': '2021-10-10T00:00:00.000+2',
                        'expected_valid_until': '2021-10-11T06:00:00.000+2',
                    },
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),

            # Passage after 6 - both day permit (valid today) and a year permit
            (
                '2021-10-10T06:30:00.000',
                [
                    {
                        'permit_type': 'Dagontheffing',
                        'valid_from': '2021-10-10T00:00:00.000',
                        'valid_until': '2021-10-10T00:00:00.000',
                        'expected_valid_from': '2021-10-10T00:00:00.000+2',
                        'expected_valid_until': '2021-10-11T06:00:00.000+2',
                    },
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),

            # Passage before 6 - both day permit (valid yesterday) and a year permit
            (
                '2021-10-10T05:30:00.000',
                [
                    {
                        'permit_type': 'Dagontheffing',
                        'valid_from': '2021-10-09T00:00:00.000',
                        'valid_until': '2021-10-09T00:00:00.000',
                        'expected_valid_from': '2021-10-09T00:00:00.000+2',
                        'expected_valid_until': '2021-10-10T06:00:00.000+2',
                    },
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),

            # Both day and route permits
            (
                '2021-10-10T05:30:00.000',
                [
                    {
                        'permit_type': 'Dagontheffing',
                        'valid_from': '2021-10-10T00:00:00.000',
                        'valid_until': '2021-10-10T00:00:00.000',
                        'expected_valid_from': '2021-10-10T00:00:00.000+2',
                        'expected_valid_until': '2021-10-11T06:00:00.000+2',
                    },
                    {
                        'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),

            # Both year and route permits
            (
                '2021-10-10T05:30:00.000',
                [
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    },
                    {
                        'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),

            # Day, year and route permits
            (
                '2021-10-10T05:30:00.000',
                [
                    {
                        'permit_type': 'Dagontheffing',
                        'valid_from': '2021-10-10T00:00:00.000',
                        'valid_until': '2021-10-10T00:00:00.000',
                        'expected_valid_from': '2021-10-10T00:00:00.000+2',
                        'expected_valid_until': '2021-10-11T06:00:00.000+2',
                    },
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    },
                    {
                        'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                        'valid_from': '2021-09-10T00:00:00.000',
                        'valid_until': '2022-09-10T00:00:00.000',
                        'expected_valid_from': '2021-09-10T00:00:00.000+2',
                        'expected_valid_until': '2022-09-11T00:00:00.000+2',
                    }
                ]
            ),
        ],
    )
    def test_get_permits_with_multiple_permits(self, mocker, passage_at, permits):
        decos_response = {
            'count': len(permits),
            'content': []
        }
        for permit_info in permits:
            permit_dict = {
                'fields': {
                    'text17': permit_info['permit_type'],
                    'subject1': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                    'date6': permit_info['valid_from'],
                    'date7': permit_info['valid_until'],
                }
            }
            decos_response['content'].append(permit_dict)
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        decos = DecosJoin()
        result = decos.get_permits('ABC123', parse(passage_at))
        expected = []
        for permit_info in permits:
            expected_permit = {
                'permit_type': permit_info['permit_type'],
                'permit_description': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                'valid_from': parse(permit_info['expected_valid_from']),
                'valid_until': parse(permit_info['expected_valid_until']),
            }
            expected.append(expected_permit)

        assert result == expected


class TestVerkeersvergunningen:
    def setup(self):
        self.URL = '/zwaarverkeer/get_permits/'
        self.test_payload = {'number_plate': '1234AB', 'passage_at': '2022-10-10T06:30:00.000'}

        self.auth_headers = create_basic_auth_headers(
            settings.CLEOPATRA_BASIC_AUTH_USER,
            settings.CLEOPATRA_BASIC_AUTH_PASS
        )

    @pytest.mark.parametrize(
        'passage_at, expected_passage_at',
        [
            ('2022-10-10T06:30:00.000', '2022-10-10T06:30:00+02:00'),  # Naive datetime
            ('2022-10-10T06:30:00+02:00', '2022-10-10T06:30:00+02:00')  # Timezone-aware datetime
        ]
    )
    def test_basics(self, client, mocker, passage_at, expected_passage_at):
        decos_response = {
            'count': 1,
            'content': [
                {
                    'fields': {
                        'text17': 'Dagontheffing',
                        'subject1': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                        'date6': '2021-10-10T00:00:00.000',
                        'date7': '2022-10-10T00:00:00.000',
                    }
                }
            ]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        payload = self.test_payload
        payload['passage_at'] = passage_at

        response = client.post(
            self.URL,
            json.dumps(self.test_payload),
            content_type='application/json',
            **self.auth_headers
        )
        assert response.status_code == 200

        decos_permit = decos_response['content'][0]['fields']
        expected = {
            'number_plate': self.test_payload['number_plate'],
            'passage_at': expected_passage_at,
            'has_permit': True,
            'permits': [
                {
                    'permit_type': decos_permit['text17'],
                    'permit_description': decos_permit['subject1'],
                    'valid_from': '2021-10-10T00:00:00+02:00',
                    'valid_until': '2022-10-11T06:00:00+02:00',
                }
            ]
        }

        response_dict = json.loads(response.content)
        assert response_dict['number_plate'] == expected['number_plate']
        assert response_dict['passage_at'] == expected['passage_at']

        assert response_dict['has_permit'] == expected['has_permit']
        response_permit = response_dict['permits'][0]
        expected_permit = expected['permits'][0]
        assert response_permit == expected_permit

    def test_other_requests_than_post(self, client):
        response = client.get(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.put(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.patch(self.URL, **self.auth_headers)
        assert response.status_code == 405
        response = client.delete(self.URL, **self.auth_headers)
        assert response.status_code == 405

    def test_no_basic_auth_credentials_supplied_by_client(self, client):
        response = client.post(self.URL, json.dumps(self.test_payload), content_type='application/json')
        assert response.status_code == 403

    def test_wrong_basic_auth_credentials_supplied_by_client(self, client):
        response = client.post(
            self.URL,
            json.dumps(self.test_payload),
            content_type='application/json',
            **create_basic_auth_headers('wrong_user', 'wrong_pass')
        )
        assert response.status_code == 403

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
