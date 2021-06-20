from odoo import api, models, fields, _


class ClickerTask(models.Model):
    _name = "clicker.task"

    space_id = fields.Many2one(comodel_name="clicker.space")
