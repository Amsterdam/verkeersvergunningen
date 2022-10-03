from requests import HTTPError


class MockResponse:
    def __init__(self, status_code, json_content=None, content=None, headers=None):
        self.status_code = status_code
        self.json_content = json_content
        self.content = content
        self.headers = headers

    def json(self):
        return self.json_content

    def raise_for_status(self):
        if str(self.status_code) != '200':
            raise HTTPError(str(self.status_code), response=self)