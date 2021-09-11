from odoo import fields, models


class ClickerTask(models.Model):
    _name = "clicker.task"

    space_id = fields.Many2one(comodel_name="clicker.space")
