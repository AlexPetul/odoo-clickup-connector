import json

from odoo import api, http, SUPERUSER_ID
from odoo.http import request
from odoo.modules.registry import Registry

from ..clickup.requests_manager import RequestsManager
from ..clickup import constants as const


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
        task_id = data["task_id"]
        space_id = request.env["clicker.webhook"].search([("webhook_id", "=", data["webhook_id"])]).space_id
        request_manager = RequestsManager(request.env, space_id.backend_id.oauth_token)
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

    @http.route([const.BASE_WEBHOOK_URL], type="json", cors="*", auth="public", website=False)
    def process_web_hook_request(self, *args, **kwargs):
        data = json.loads(request.httprequest.data.decode("UTF-8"))
        self.get_method_by_event(data["event"])(data)

    @classmethod
    def create_web_hooks(cls, fields: dict, db_name: str, token: str, team_id: str) -> None:
        db_registry = Registry.new(db_name=db_name)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env = api.Environment(cr=cr, uid=SUPERUSER_ID, context={})

            base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
            web_hook_url = f"{base_url}{const.BASE_WEBHOOK_URL}"
            events = [value for key, value in cls.web_hooks_mapping.items() if key in fields]

            request_manager = RequestsManager(env, token)
            response, status = request_manager.create_web_hook(team_id, {"endpoint": web_hook_url, "events": events})
            if status == 200:
                env["clicker.webhook"].create({
                    "webhook_id": response["id"]
                })

    @classmethod
    def process_web_hooks(cls, fields: dict, db_name: str, token: str, webhooks: list):
        db_registry = Registry.new(db_name=db_name)
        with api.Environment.manage(), db_registry.cursor() as cr:
            env = api.Environment(cr=cr, uid=SUPERUSER_ID, context={})
            base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
            for hook in webhooks:
                if base_url in hook["endpoint"]:
                    for field, enable in fields.items():
                        event = cls.web_hooks_mapping[field]
                        if enable:
                            hook["events"].append(event)
                        else:
                            hook["events"].remove(event)

                    request_manager = RequestsManager(env, token)
                    data = {"endpoint": hook["endpoint"], "status": "active", "events": hook["events"]}
                    response, status = request_manager.update_web_hook(hook["id"], data)
                    break

