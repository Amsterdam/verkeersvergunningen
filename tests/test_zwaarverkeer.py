import base64
import json
from datetime import date, timedelta

import pytest
from dateutil import parser
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

class TestDecosJoin:
    def setup(self):
        pass

    @pytest.mark.parametrize(
        'passage_at, permit_type, date_from, date_until',
        [
            # Year permit
            (
                '2021-10-10T06:30:00.000',
                'Jaarontheffing gewicht en ondeelbaar',
                '2021-09-10T00:00:00.000',
                '2022-09-10T00:00:00.000',
            ),

            # day permit today, passage before 6
            (
                '2021-10-10T05:30:00.000',
                'Dagontheffing',
                '2021-10-10T00:00:00.000',
                '2022-10-10T00:00:00.000',
            ),

            # day permit today, passage after 6
            (
                '2021-10-10T06:30:00.000',
                'Dagontheffing',
                '2021-10-10T00:00:00.000',
                '2022-10-10T00:00:00.000',
            ),

            # day permit yesterday, passage before 6
            (
                '2021-10-10T05:30:00.000',
                'Dagontheffing',
                '2021-10-09T00:00:00.000',
                '2022-10-09T00:00:00.000',
            ),

            # day permit yesterday, passage after 6:
            # this would give no result from the endpoint, so no test for this one

            # route permit today
            (
                '2021-10-10T06:30:00.000',
                'Routeontheffing gewicht en ondeelbaar',
                '2021-10-10T00:00:00.000',
                '2022-10-10T00:00:00.000',
            ),
        ],
    )
    def test_get_permits_with_a_single_permit(self, mocker, passage_at, permit_type, date_from, date_until):
        decos_response = {
            'count': 1,
            'content': [
                {
                    'fields': {
                        'text17': permit_type,
                        'subject1': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                        'date6': date_from,
                        'date7': date_until,
                    }
                }
            ]
        }
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        decos = DecosJoin()
        result = decos.get_permits('ABC123', parser.parse(passage_at))
        expected = [{
            'permit_type': permit_type,
            'permit_description': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
            'valid_from': date_from,
            'valid_until': date_until,
        }]
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
                        'date_from': '2021-10-10T00:00:00.000',
                        'date_until': '2022-10-10T00:00:00.000',
                    },
                    {
                        'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                        'date_from': '2021-09-10T00:00:00.000',
                        'date_until': '2022-09-10T00:00:00.000',
                    }
                ]
            ),

            # Passage after 6 - both day permit (valid today) and a year permit
            (
                    '2021-10-10T06:30:00.000',
                    [
                        {
                            'permit_type': 'Dagontheffing',
                            'date_from': '2021-10-10T00:00:00.000',
                            'date_until': '2022-10-10T00:00:00.000',
                        },
                        {
                            'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        }
                    ]
            ),

            # Passage before 6 - both day permit (valid yesterday) and a year permit
            (
                    '2021-10-10T05:30:00.000',
                    [
                        {
                            'permit_type': 'Dagontheffing',
                            'date_from': '2021-10-09T00:00:00.000',
                            'date_until': '2022-10-09T00:00:00.000',
                        },
                        {
                            'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        }
                    ]
            ),

            # Both day and route permits
            (
                    '2021-10-10T05:30:00.000',
                    [
                        {
                            'permit_type': 'Dagontheffing',
                            'date_from': '2021-10-10T00:00:00.000',
                            'date_until': '2022-10-10T00:00:00.000',
                        },
                        {
                            'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        }
                    ]
            ),

            # Both year and route permits
            (
                    '2021-10-10T05:30:00.000',
                    [
                        {
                            'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        },
                        {
                            'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        }
                    ]
            ),

            # Day, year and route permits
            (
                    '2021-10-10T05:30:00.000',
                    [
                        {
                            'permit_type': 'Dagontheffing',
                            'date_from': '2021-10-10T00:00:00.000',
                            'date_until': '2022-10-10T00:00:00.000',
                        },
                        {
                            'permit_type': 'Jaarontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
                        },
                        {
                            'permit_type': 'Routeontheffing gewicht en ondeelbaar',
                            'date_from': '2021-09-10T00:00:00.000',
                            'date_until': '2022-09-10T00:00:00.000',
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
                    'date6': permit_info['date_from'],
                    'date7': permit_info['date_until'],
                }
            }
            decos_response['content'].append(permit_dict)
        mock_response = MockResponse(200, json_content=decos_response)
        mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)

        decos = DecosJoin()
        result = decos.get_permits('ABC123', parser.parse(passage_at))
        expected = []
        for permit_info in permits:
            expected_permit = {
                'permit_type': permit_info['permit_type'],
                'permit_description': 'Ontheffing 7,5 ton Binnenstad ABC123, DEF456, GEJ789',
                'valid_from': permit_info['date_from'],
                'valid_until': permit_info['date_until'],
            }
            expected.append(expected_permit)

        assert result == expected


class TestVerkeersvergunningen:
    def setup(self):
        self.URL = '/zwaarverkeer/has_permit/'
        self.test_payload = {'number_plate': '1234AB', 'passage_at': '2022-01-01T13:00:00.000'}

        # Basic auth
        credentials = f"{settings.CLEOPATRA_BASIC_AUTH_USER}:{settings.CLEOPATRA_BASIC_AUTH_PASS}"
        auth_string = 'Basic ' + base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self.auth_headers = {'HTTP_AUTHORIZATION': auth_string}

    # @pytest.mark.parametrize(
    #     'decos_count,expected_has_permit',
    #     [
    #         (0, False),
    #         (1, True),
    #         (2, True),
    #     ]
    # )
    # def test_basics(self, client, mocker, decos_count, expected_has_permit):
    #     mock_response = MockResponse(200, json_content={'count': decos_count})
    #     mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)
    #
    #     response = client.post(
    #         self.URL,
    #         json.dumps(self.test_payload),
    #         content_type='application/json',
    #         **self.auth_headers
    #     )
    #     assert response.status_code == 200
    #     assert json.loads(response.content)['number_plate'] == self.test_payload['number_plate']
    #     assert json.loads(response.content)['has_permit'] == expected_has_permit
    #     # assert json.loads(response.content)['date_from'] == date.today().isoformat()
    #     # assert json.loads(response.content)['date_until'] == (date.today() + timedelta(days=1)).isoformat()

#     def test_other_requests_than_post(self, client):
#         response = client.get(self.URL, **self.auth_headers)
#         assert response.status_code == 405
#         response = client.put(self.URL, **self.auth_headers)
#         assert response.status_code == 405
#         response = client.patch(self.URL, **self.auth_headers)
#         assert response.status_code == 405
#         response = client.delete(self.URL, **self.auth_headers)
#         assert response.status_code == 405
#
#     def test_no_basic_auth_credentials_supplied_by_client(self, client, mocker):
#         response = client.post(self.URL, json.dumps(self.test_payload), content_type='application/json')
#         assert response.status_code == 403
#
#     def test_wrong_basic_auth_credentials_supplied_by_client(self, client, mocker):
#         response = client.post(
#             self.URL,
#             json.dumps(self.test_payload),
#             content_type='application/json',
#             HTTP_AUTHORIZATION='Basic wrong:wrong'
#         )
#         assert response.status_code == 403
#
#     def test_wrong_basic_auth_credentials_for_decos(self, client, mocker):
#         mock_response = MockResponse(401)
#         mocker.patch('zwaarverkeer.views.DecosJoin._do_request', return_value=mock_response)
#
#         response = client.post(
#             self.URL,
#             json.dumps(self.test_payload),
#             content_type='application/json',
#             **self.auth_headers
#         )
#         assert response.status_code == 502
#
#     def test_invalid_json(self, client):
#         response = client.post(
#             self.URL,
#             'invalid json',
#             content_type='application/json',
#             **self.auth_headers
#         )
#         assert response.status_code == 400
#
#     # def test_missing_number_plate(self, client):
#     #     payload_without_number_plate = self.test_payload
#     #     del payload_without_number_plate['number_plate']
#     #     response = client.post(
#     #         self.URL,
#     #         json.dumps(self.test_payload),
#     #         content_type='application/json',
#     #         **self.auth_headers
#     #     )
#     #     breakpoint()
#     #     assert response.status_code == 200
#
#
#     def test_when_decos_is_not_available(self, client):
#         # response = client.post(self.URL, json.dumps(self.test_payload), content_type='application/json')
#         # assert response.status_code == 502
#         pass
