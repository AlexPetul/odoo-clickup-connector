import asyncio
from datetime import datetime
from typing import Union

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..clickup.requests_manager import RequestsManager
from ..controllers.webhooks import WebHookManager


class ClickerWebhook(models.Model):
    _name = "clicker.webhook"

    webhook_id = fields.Char()
    space_id = fields.Many2one(comodel_name="clicker.space")


class ClickerSpace(models.Model):
    _name = "clicker.space"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Click Up space model"

    name = fields.Char(string="Name")
    color = fields.Integer(string="Color Index")
    clicker_backend_id = fields.Many2one(comodel_name="clicker.backend", string="Workspace", readonly=True, copy=False)
    clicker_id = fields.Char(string="Clickup ID", size=32, readonly=True, copy=False)
    team_id = fields.Char(string="Team ID", size=32, readonly=True, copy=False)
    task_ids = fields.One2many(comodel_name="clicker.task", inverse_name="space_id", string="Tasks", copy=False)
    imported_tasks_count = fields.Integer(string="Tasks", compute="_compute_imported_tasks_count", copy=False)
    is_private = fields.Boolean(string="Private", default=False, readonly=True)
    time_tracking = fields.Boolean(string="Time Tracking", default=False, readonly=True)
    default_status = fields.Many2one(string="Default Status", comodel_name="project.task.type",
                                     help="If status name do not exist in Odoo, task will be moved to this status.")

    task_created_hook = fields.Boolean(string="Task Created", default=False, copy=False)
    task_updated_hook = fields.Boolean(string="Task Updated", default=False, copy=False)
    task_deleted_hook = fields.Boolean(string="Task Deleted", default=False, copy=False)

    def unlink(self) -> bool:
        request_manager = RequestsManager(self.env, self.clicker_backend_id.oauth_token)
        for record in self:
            for webhook in self.env["clicker.webhook"].search([("space_id", "=", record.clicker_id)]):
                request_manager.delete_web_hook(webhook.webhook_id)
        return super().unlink()

    def write(self, vals: dict) -> bool:
        hook_fields = {key: val for key, val in vals.items() if "hook" in key}
        if hook_fields:
            request_manager = RequestsManager(self.env, self.clicker_backend_id.oauth_token)
            response, status = request_manager.get_web_hooks_by_team_id(self.team_id)
            if status == 200:
                if not response["webhooks"]:
                    WebHookManager.create_web_hooks(
                        fields=hook_fields, db_name=self.env.cr.dbname, space_id=self.clicker_id,
                        team_id=self.team_id, token=self.clicker_backend_id.oauth_token
                    )
                else:
                    WebHookManager.process_web_hooks(
                        fields=hook_fields, db_name=self.env.cr.dbname, space_id=self.clicker_id,
                        team_id=self.team_id, token=self.clicker_backend_id.oauth_token, webhooks=response["webhooks"]
                    )
        return super().write(vals)

    @staticmethod
    def _fetch_lists(request_manager: RequestsManager, clicker_space_id: str) -> list:
        response, status = request_manager.get_lists_by_space_id(clicker_space_id)
        if status == 200:
            return list(filter(lambda x: int(x["task_count"]) > 0, response.get("lists", [])))

    @staticmethod
    def _fetch_folder_lists(request_manager: RequestsManager, clicker_space_id: str) -> list:
        lists = list()
        response, status = request_manager.get_folders_by_space_id(clicker_space_id)
        if status == 200:
            folders = response.get("folders", [])
            for folder in folders:
                response, status = request_manager.get_lists_by_folder_id(folder["id"])
                if status == 200:
                    lists.append(*response.get("lists"))
        return lists

    def get_tasks_hierarchy(self) -> list:
        request_manager = RequestsManager(self.env, self.clicker_backend_id.token or self.clicker_backend_id.oauth_token)
        folder_lists = self._fetch_folder_lists(request_manager, self.clicker_id)
        raw_lists = self._fetch_lists(request_manager, self.clicker_id)
        clicker_lists = folder_lists + raw_lists
        existing_ids = self.env["project.task"].search([]).mapped("clicker_task_id")
        for clicker_list in clicker_lists:
            response, status = request_manager.get_tasks_by_list_id(clicker_list["id"])
            if status == 200:
                clicker_list["tasks"] = list(filter(lambda x: x["id"] not in existing_ids, response.get("tasks", [])))
        result = list(filter(lambda x: x["tasks"], clicker_lists))
        if not result:
            raise UserError(_("Nothing to import."))
        return result

    @staticmethod
    def get_datetime_from_unix_timestamp(timestamp: str) -> Union[datetime, bool]:
        try:
            return datetime.fromtimestamp(int(timestamp) / 1000)
        except (TypeError, Exception):
            return False

    def get_user_by_username_or_email(self, clicker_user: dict) -> Union[int, bool]:
        try:
            return self.env["res.users"].search([
                "|",
                ("email", "=", clicker_user["email"]),
                ("login", "=", clicker_user["email"]),
                ("name", "ilike", clicker_user["username"])
            ], limit=1).id
        except (AttributeError, Exception):
            return False

    def import_tasks(self, task_ids: list) -> None:
        if not task_ids:
            raise UserError(_("Please, choose at least one task or press 'Discard'."))

        request_manager = RequestsManager(self.env, self.clicker_backend_id.token or self.clicker_backend_id.oauth_token)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        ProjectTask = self.env["project.task"]
        ProjectTaskType = self.env["project.task.type"]
        for task_id in task_ids:
            clicker_task = loop.run_until_complete(request_manager.get_task_by_task_id_async(task_id))
            if not ProjectTask.search_count([("clicker_task_id", "=", clicker_task["id"])]):
                status = ProjectTaskType.search([("name", "ilike", clicker_task["status"]["status"])], limit=1)
                due_date = self.get_datetime_from_unix_timestamp(clicker_task["due_date"])
                assignee_id = self.get_user_by_username_or_email(next(iter(clicker_task["assignees"]), False))

                ProjectTask.create({
                    "clicker_task_id": clicker_task["id"],
                    "clicker_space_id": clicker_task["space"]["id"],
                    "name": clicker_task["name"],
                    "stage_id": status.id or self.default_status.id,
                    "description": clicker_task["description"],
                    "date_deadline": due_date,
                    "user_id": assignee_id
                })

    def _compute_imported_tasks_count(self) -> None:
        ProjectTask = self.env["project.task"]
        for record in self:
            record.imported_tasks_count = ProjectTask.search_count([("clicker_space_id", "=", record.clicker_id)])

    def action_open_imported_tasks(self) -> dict:
        return {
            "name": _("Tasks"),
            "type": "ir.actions.act_window",
            "view_mode": "kanban,form",
            "res_model": "project.task",
            "target": "current",
            "views": [
                (self.env.ref("project.view_task_kanban").id, "kanban"),
                (self.env.ref("project.view_task_form2").id, "form")
            ],
            "domain": [("clicker_space_id", "=", self.clicker_id)]
        }

