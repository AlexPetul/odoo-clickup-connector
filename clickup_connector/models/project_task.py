from odoo import _, api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    clicker_space_id = fields.Char(size=32)
    clicker_task_id = fields.Char(size=32, readonly=True)
