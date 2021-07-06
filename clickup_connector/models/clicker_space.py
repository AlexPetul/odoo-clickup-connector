from odoo import api, models, fields, _
from itertools import groupby
import asyncio

from ..service.requests_manager import RequestsManager


class ClickerSpace(models.Model):
    _name = "clicker.space"

    name = fields.Char(string="Name")
    color = fields.Integer(string="Color Index")
    clicker_backend_id = fields.Many2one(comodel_name="clicker.backend", string="Workspace")
    clicker_id = fields.Char()
    owner_id = fields.Many2one(comodel_name="res.users", string="Owner")
    task_ids = fields.One2many(comodel_name="clicker.task", inverse_name="space_id", string="Tasks")
    task_ids_count = fields.Integer(string="Tasks Count")
    folders_count = fields.Integer(string="Folders")
    task_lists_count = fields.Integer(string="Lists")
    imported_tasks_count = fields.Integer()
    is_private = fields.Boolean(string="Private", default=False, readonly=True)
    time_tracking = fields.Boolean(string="Time Tracking", default=False, readonly=True)

    task_created = fields.Boolean(default=False)
    task_updated = fields.Boolean(default=False)
    task_deleted = fields.Boolean(default=False)

    @staticmethod
    def _fetch_lists(request_manager, clicker_space_id):
        response, status = request_manager.get_lists_by_space_id(clicker_space_id)
        if status == 200:
            return response.get("lists", [])

    @staticmethod
    def _fetch_folder_lists(request_manager, clicker_space_id):
        lists = list()
        response, status = request_manager.get_folders_by_space_id(clicker_space_id)
        if status == 200:
            folders = response.get("folders", [])
            for folder in folders:
                response, status = request_manager.get_lists_by_folder_id(folder["id"])
                if status == 200:
                    lists.append(*response.get("lists"))
        return lists

    def get_tasks_hierarchy(self):
        request_manager = RequestsManager(self.env, self.clicker_backend_id.token)
        folder_lists = self._fetch_folder_lists(request_manager, self.clicker_id)
        raw_lists = self._fetch_lists(request_manager, self.clicker_id)
        clicker_lists = [*folder_lists, *raw_lists]
        for clicker_list in clicker_lists:
            response, status = request_manager.get_tasks_by_list_id(clicker_list["id"])
            if status == 200:
                clicker_list["tasks"] = response.get("tasks", [])
        return clicker_lists

    def import_tasks(self, task_ids):
        request_manager = RequestsManager(self.env, self.clicker_backend_id.token)

        loop = None
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        finally:
            for task_id in task_ids:
                response = loop.run_until_complete(request_manager.get_task_by_task_id_async(task_id))
                print(response)

    def action_open_imported_tasks(self):
        pass

