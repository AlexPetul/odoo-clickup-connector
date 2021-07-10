from odoo import http
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

from ..service.requests_manager import RequestsManager


class WebHookManager(http.Controller):

    web_hooks_mapping = {
        "task_created_hook": "taskCreated",
        "task_updated_hook": "taskUpdated",
        "task_deleted_hook": "taskDeleted"
    }

    @classmethod
    def create_web_hooks(cls, fields: dict, db_name: str, token: str, team_id: str):
        db_registry = Registry.new(db_name)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            request_manager = RequestsManager(env, token)
            events = [value for key, value in cls.web_hooks_mapping.items() if key in fields]
            response, status = request_manager.create_web_hook(team_id, {"events": events})
            print(response)

    @classmethod
    def process_web_hooks(cls, fields: dict, db_name: str, token: str):
        print(fields)
