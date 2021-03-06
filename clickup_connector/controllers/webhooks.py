import json

from odoo import http
from odoo.http import request

from ..clickup import constants as const
from ..clickup.decorators import api_method
from ..clickup.requests_manager import RequestsManager


class WebHookManager(http.Controller):

    web_hooks_mapping = {
        "task_created_hook": "taskCreated",
        "task_updated_hook": "taskUpdated",
        "task_deleted_hook": "taskDeleted"
    }

    def get_method_by_event(self, event: str) -> callable:
        methods = {
            "taskCreated": self.create_task_hook,
            "taskUpdated": self.update_task_hook,
            "taskDeleted": self.delete_task_hook
        }

        return methods[event]

    @api_method
    def create_task_hook(self, data: dict) -> None:
        task_id = data["task_id"]
        space_id = self.env["clicker.webhook"].search([("webhook_id", "=", data["webhook_id"])]).space_id
        request_manager = RequestsManager(self.env, space_id.clicker_backend_id.oauth_token)
        response, status = request_manager.get_task_by_id(task_id)
        if status == 200:
            space_id = response["space"]["id"]
            self.env["clicker.space"].search([("clicker_id", "=", space_id)], limit=1).import_tasks([task_id])

    @api_method
    def update_task_hook(self, data: dict) -> None:
        task_id = self.env["project.task"].search([("clicker_task_id", "=", data["task_id"])], limit=1)
        space_id = self.env["clicker.webhook"].search([("webhook_id", "=", data["webhook_id"])]).space_id
        request_manager = RequestsManager(self.env, space_id.clicker_backend_id.oauth_token)
        task, status = request_manager.get_task_by_id(task_id.clicker_task_id)
        if status == 200:
            space = self.env["clicker.space"].search([("clicker_id", "=", task["space"]["id"])], limit=1)
            task_data = {
                "stage_id": self.env["project.task.type"].search([("name", "ilike", task["status"]["status"])], limit=1),
                "date_deadline": space.get_datetime_from_unix_timestamp(task["due_date"]),
                "user_id": space.get_user_by_username_or_email(next(iter(task["assignees"]), False)),
                "description": task["description"],
                "name": task["name"]
            }

            for field, value in task_data.items():
                if getattr(task_id, field) != value:
                    task_id.write({field: value})

    @api_method
    def delete_task_hook(self, data: dict) -> None:
        self.env["project.task"].search([("clicker_task_id", "=", data["task_id"])], limit=1).sudo().unlink()

    @http.route(const.BASE_WEBHOOK_URL, type="json", cors="*", auth="public", website=False)
    def process_web_hook_request(self, *args, **kwargs) -> None:
        data = json.loads(request.httprequest.data.decode("UTF-8"))
        self.get_method_by_event(data["event"])(data)

    @classmethod
    @api_method
    def create_web_hooks(cls, **kwargs) -> None:
        base_url = cls.env["ir.config_parameter"].sudo().get_param("web.base.url")
        web_hook_url = f"{base_url}{const.BASE_WEBHOOK_URL}"
        events = [value for key, value in cls.web_hooks_mapping.items() if key in kwargs["fields"]]

        request_manager = RequestsManager(cls.env, kwargs["token"])
        response, status = request_manager.create_web_hook(kwargs["team_id"], {"endpoint": web_hook_url, "events": events})
        if status == 200:
            cls.env["clicker.webhook"].create({
                "webhook_id": response["id"],
                "space_id": kwargs["space_id"]
            })

    @classmethod
    @api_method
    def process_web_hooks(cls, **kwargs) -> None:
        base_url = cls.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for hook in kwargs["webhooks"]:
            if base_url in hook["endpoint"]:
                for field, enable in kwargs["fields"].items():
                    event = cls.web_hooks_mapping[field]
                    if enable:
                        hook["events"].append(event)
                    else:
                        hook["events"].remove(event)

                request_manager = RequestsManager(cls.env, kwargs["token"])
                request_manager.update_web_hook(hook["id"], data={
                    "endpoint": hook["endpoint"], "status": "active", "events": hook["events"]
                })
                return None
