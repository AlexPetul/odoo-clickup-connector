import requests
import json


class RequestsManager:

    @staticmethod
    def execute_get(base_uri, relative_uri, params=None, token=None, **kwargs):
        headers = {"Authorization": token}
        response = requests.get(f'{base_uri}/{relative_uri}', headers=headers)
        return json.loads(response.text), response.status_code
