import json
from datetime import date, timedelta


class TestVerkeersvergunningen:
    def setup(self):
        self.URL = '/zwaarverkeer/'

    def test_vanilla(self, client):
        payload = {'number_plate': '1234AB'}

        response = client.post(self.URL, json.dumps(payload), content_type='application/json')

        assert response.status_code == 200
        assert json.loads(response.content)['number_plate'] == payload['number_plate']
        assert json.loads(response.content)['has_permit'] == True
        # assert json.loads(response.content)['date_from'] == date.today().isoformat()
        # assert json.loads(response.content)['date_until'] == (date.today() + timedelta(days=1)).isoformat()
