import logging
from typing import Union

import aiohttp
import requests
from odoo import _
from odoo.api import Environment
from odoo.exceptions import UserError
from .exceptions import ClickupApiException

_logger = logging.getLogger(__name__)
persistent_session = requests.Session()


class RequestsManager:
    __slots__ = ["_base_api_uri", "_headers"]

    def __init__(self, env: Environment, token: str = None) -> None:
        self._base_api_uri = env["ir.config_parameter"].sudo().get_param("clickup_connector.clicker_api_uri")
        self._headers = {
            "Accept": "application/json, text/html",
            "Content-Type": "application/json",
            "Authorization": token
        }

    def __repr__(self):
        return f"{self.__class__.__name__}({self._base_api_uri})"

    async def execute_async_request(self, relative_path: str) -> dict:
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.get(url=f"{self._base_api_uri}{relative_path}") as async_resp:
                return await async_resp.json()

    def execute_request(self, relative_path: str, method: str = "GET", body: dict = None, params: dict = None) -> Union[tuple, None]:
        try:
            response = persistent_session.request(
                method=method,
                url=f"{self._base_api_uri}{relative_path}",
                headers=self._headers,
                json=body,
                params=params
            )
            _logger.info("Request sent to %s %d", response.url, response.status_code)
        except ClickupApiException as e:
            raise ClickupApiException(e)
        except Exception as e:
            raise UserError(_(e))

        return response.json(), response.status_code

    def get_teams(self) -> Union[tuple, None]:
        return self.execute_request("team")

    def get_access_token(self, params: dict) -> Union[tuple, None]:
        return self.execute_request("oauth/token", method="POST", params=params)

    def update_web_hook(self, webhook_id: str, data: dict) -> Union[tuple, None]:
        return self.execute_request(f"webhook/{webhook_id}", method="PUT", body=data)

    def delete_web_hook(self, webhook_id: str) -> Union[tuple, None]:
        return self.execute_request(f"webhook/{webhook_id}", method="DELETE")

    def create_web_hook(self, team_id, endpoints: dict) -> Union[tuple, None]:
        return self.execute_request(f"team/{team_id}/webhook", method="POST", body=endpoints)

    def get_web_hooks_by_team_id(self, team_id: str) -> Union[tuple, None]:
        return self.execute_request(f"team/{team_id}/webhook")

    async def get_task_by_task_id_async(self, task_id: str) -> dict:
        return await self.execute_async_request(f"task/{task_id}")

    def get_task_by_id(self, task_id: str) -> Union[tuple, None]:
        return self.execute_request(f"task/{task_id}")

    def get_tasks_by_list_id(self, list_id: str) -> Union[tuple, None]:
        return self.execute_request(f"list/{list_id}/task")

    def get_spaces_by_team_id(self, team_id: str) -> Union[tuple, None]:
        return self.execute_request(f"team/{team_id}/space")

    def get_folders_by_space_id(self, space_id: str) -> Union[tuple, None]:
        return self.execute_request(f"space/{space_id}/folder")

    def get_lists_by_folder_id(self, folder_id: str) -> Union[tuple, None]:
        return self.execute_request(f"folder/{folder_id}/list")

    def get_lists_by_space_id(self, space_id: str) -> Union[tuple, None]:
        return self.execute_request(f"space/{space_id}/list")
