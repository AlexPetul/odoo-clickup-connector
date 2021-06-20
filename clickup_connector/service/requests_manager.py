import requests
from odoo import _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)
persistent_session = requests.Session()


class RequestsManager:

    def __init__(self, env, token):
        self._base_api_uri = env["ir.config_parameter"].sudo().get_param("clickup_connector.clicker_api_uri")
        self._headers = {"Accept": "application/json, text/html", "Authorization": token}

    def execute_request(self, relative_path, params=None):
        try:
            response = persistent_session.get(
                url=f"{self._base_api_uri}{relative_path}",
                params=params,
                headers=self._headers
            )
            _logger.info("Request sent to %s %d", response.url, response.status_code)
        except requests.exceptions.RequestException as e:
            _logger.error("Request failed: %s" % e.response)
            raise UserError(_("Something went wrong while sending request. Please, try again."))

        return response.json(), response.status_code

    def get_teams(self):
        return self.execute_request("team")

    def get_spaces_by_team_id(self, team_id):
        return self.execute_request(f"team/{team_id}/space")

    def get_folders_by_space_id(self, space_id):
        return self.execute_request(f"space/{space_id}/folder")

    def get_lists_by_folder_id(self, folder_id):
        return self.execute_request(f"folder/{folder_id}/list")

    def get_lists_by_space_id(self, space_id):
        return self.execute_request(f"space/{space_id}/list")
