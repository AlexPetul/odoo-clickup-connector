from odoo import api, models, fields, _


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
