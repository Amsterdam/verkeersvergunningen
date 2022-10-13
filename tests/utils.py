from json import JSONDecodeError
from requests import JSONDecodeError as RequestsJSONDecodeError

from requests import HTTPError
import json


class MockResponse:
    def __init__(self, status_code, json_content=None, content=None, headers=None):
        self.status_code = status_code
        self.json_content = json_content
        self.content = content
        self.headers = headers

    def json(self, **kwargs):
        if self.json_content:
            return self.json_content

        try:
            return json.loads(self.content, **kwargs)
        except JSONDecodeError as e:
            raise RequestsJSONDecodeError(e.msg, e.doc, e.pos)

    def raise_for_status(self):
        if str(self.status_code) != '200':
            raise HTTPError(str(self.status_code), response=self)
