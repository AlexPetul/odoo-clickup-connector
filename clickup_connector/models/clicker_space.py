import asyncio
from datetime import datetime
from typing import Union

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..service.requests_manager import RequestsManager
from ..controllers.webhooks import WebHookManager


class ClickerSpace(models.Model):
    _name = "clicker.space"
    _description = "Click Up space model"

    name = fields.Char(string="Name")
    color = fields.Integer(string="Color Index")
    clicker_backend_id = fields.Many2one(comodel_name="clicker.backend", string="Workspace", readonly=True)
    clicker_id = fields.Char(size=32, readonly=True)
    team_id = fields.Char(size=32, readonly=True)
    task_ids = fields.One2many(comodel_name="clicker.task", inverse_name="space_id", string="Tasks")
    imported_tasks_count = fields.Integer(string="Tasks", compute="_compute_imported_tasks_count")
    is_private = fields.Boolean(string="Private", default=False, readonly=True)
    time_tracking = fields.Boolean(string="Time Tracking", default=False, readonly=True)
    default_status = fields.Many2one(string="Default Status", comodel_name="project.task.type",
                                     help="If status name wasn't found in Odoo, then task will be moved to this status.")
    log_ids = fields.One2many(comodel_name="clicker.log", inverse_name="space_id", readonly="1", copy=False)
    task_created_hook = fields.Boolean(string="Task Created", default=False)
    task_updated_hook = fields.Boolean(string="Task Updated", default=False)
    task_deleted_hook = fields.Boolean(string="Task Deleted", default=False)

    def write(self, vals: dict) -> bool:
        hook_fields = {key: val for key, val in vals.items() if "hook" in key}
        if hook_fields:
            request_manager = RequestsManager(self.env, self.clicker_backend_id.oauth_token)
            response, status = request_manager.get_web_hooks_by_team_id(self.team_id)
            print(response)
            if status == 200:
                WebHookManager.create_web_hooks(hook_fields, self.env.cr.dbname, self.clicker_backend_id.oauth_token, self.team_id)

        return super().write(vals)

    @staticmethod
    def _fetch_lists(request_manager: RequestsManager, clicker_space_id: str) -> list:
        response, status = request_manager.get_lists_by_space_id(clicker_space_id)
        if status == 200:
            return response.get("lists", [])

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
        request_manager = RequestsManager(self.env, self.clicker_backend_id.token)
        folder_lists = self._fetch_folder_lists(request_manager, self.clicker_id)
        raw_lists = self._fetch_lists(request_manager, self.clicker_id)
        clicker_lists = [*folder_lists, *raw_lists]
        for clicker_list in clicker_lists:
            response, status = request_manager.get_tasks_by_list_id(clicker_list["id"])
            if status == 200:
                clicker_list["tasks"] = response.get("tasks", [])
        return clicker_lists

    @staticmethod
    def _get_datetime_from_unix_timestamp(timestamp: str) -> Union[datetime, bool]:
        try:
            return datetime.fromtimestamp(int(timestamp) / 1000)
        except (TypeError, Exception):
            return False

    def _get_user_by_username_or_email(self, clicker_users: list) -> Union[int, bool]:
        try:
            return self.env["res.users"].search([
                "|",
                ("email", "=", clicker_users[0]["email"]),
                ("login", "=", clicker_users[0]["email"]),
                ("name", "ilike", clicker_users[0]["username"])
            ], limit=1).id
        except (IndexError, AttributeError, Exception):
            return False

    def import_tasks(self, task_ids: list) -> None:
        if not task_ids:
            raise UserError(_("Please, choose at least one task or press 'Discard'."))

        request_manager = RequestsManager(self.env, self.clicker_backend_id.token)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        ProjectTask = self.env["project.task"]
        ProjectTaskType = self.env["project.task.type"]
        for task_id in task_ids:
            clicker_task = loop.run_until_complete(request_manager.get_task_by_task_id_async(task_id))
            if not ProjectTask.search_count([("clicker_task_id", "=", clicker_task["id"])]):
                status = ProjectTaskType.search([("name", "ilike", clicker_task["status"]["status"])], limit=1)
                due_date = self._get_datetime_from_unix_timestamp(clicker_task["due_date"])
                assignee_id = self._get_user_by_username_or_email(clicker_task["assignees"])

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

