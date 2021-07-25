import json

from odoo import http
from odoo.http import request
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

from ..service.requests_manager import RequestsManager


class WebHookManager(http.Controller):

    web_hooks_mapping = {
        "task_created_hook": "taskCreated",
        "task_updated_hook": "taskUpdated",
        "task_deleted_hook": "taskDeleted"
    }

    def get_method_by_event(self, event):
        methods = {
            "taskCreated": self.create_task_hook,
            "taskUpdated": self.update_task_hook,
            "taskDeleted": self.delete_task_hook
        }

        return methods[event]

    @staticmethod
    def create_task_hook(data: dict) -> None:
        request_manager = RequestsManager(request.env)
        task_id = data["task_id"]
        response, status = request_manager.get_task_by_id(task_id)
        if status == 200:
            space_id = response["space"]["id"]
            request.env["clicker.space"].search([("clicker_id", "=", space_id)], limit=1).import_tasks([task_id])

    @staticmethod
    def update_task_hook(data: dict) -> None:
        pass

    @staticmethod
    def delete_task_hook(data: dict) -> None:
        request.env["project.task"].search([("clicker_task_id", "=", data["task_id"])], limit=1).unlink()

    @http.route(["/clicker/webhook"], type="http", cors="*", auth="public", website=False)
    def process_web_hook_request(self, *args, **kwargs):
        data = json.loads(request.httprequest.data.decode("UTF-8"))
        self.get_method_by_event(data["event"])(data)
        # a = {
        #     'event': 'taskCreated',
        #     'history_items': [
        #         {
        #             'id': '2530114621088542218',
        #             'type': 1,
        #             'date': '1626602722857',
        #             'field': 'status',
        #             'parent_id': '63436226',
        #             'data': {'status_type': 'open'},
        #             'source': None,
        #             'user': {
        #                 'id': 10887651,
        #                 'username': 'Alexey Petul',
        #                 'email': 'lexapetulcsgogo@mail.ru',
        #                 'color': '#622aea',
        #                 'initials': 'AP',
        #                 'profilePicture': None
        #             },
        #             'before': {'status': None, 'color': '#000000', 'type': 'removed', 'orderindex': -1},
        #             'after': {'status': 'to do', 'color': '  # d3d3d3', 'orderindex': 0, 'type': 'open'}
        #         },
        #         {
        #             'id': '2530114621038210569',
        #             'type': 1,
        #             'date': '1626602722857',
        #             'field': 'task_creation',
        #             'parent_id': '63436226',
        #             'data': {},
        #             'source': None,
        #             'user': {'id': 10887651, 'username': 'Alexey Petul', 'email': 'lexapetulcsgogo@mail.ru',
        #               'color': '  # 622aea', 'initials': 'AP', 'profilePicture': None}, 'before': None, 'after': None}
        #     ],
        #     'task_id': 'p7gbg7', 'webhook_id': 'b74c83ae-c6e7-46f0-bd50-7584e5ade03f'
        # }

    @classmethod
    def create_web_hooks(cls, fields: dict, db_name: str, token: str, team_id: str):
        db_registry = Registry.new(db_name)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            request_manager = RequestsManager(env, token)
            events = [value for key, value in cls.web_hooks_mapping.items() if key in fields]
            base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
            web_hook_url = f"{base_url}/clicker/webhook"
            response, status = request_manager.create_web_hook(team_id, {"endpoint": web_hook_url, "events": events})
            print(response, events)

    @classmethod
    def process_web_hooks(cls, fields: dict, db_name: str, token: str):
        pass
