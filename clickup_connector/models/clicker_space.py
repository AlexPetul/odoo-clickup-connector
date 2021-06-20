from odoo import api, models, fields, _


class ClickerSpace(models.Model):
    _name = "clicker.space"

    name = fields.Char(string="Name")
    clicker_backend_id = fields.Many2one(comodel_name="clicker.backend")
    clicker_id = fields.Char()
    color = fields.Integer(string='Color Index')
