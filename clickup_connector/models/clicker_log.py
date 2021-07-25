from odoo import models, fields, api, _


class ClickerLog(models.Model):
    _name = "clicker.log"

    space_id = fields.Many2one(comodel_name="clicker.space", string="Space")
    date = fields.Datetime(string="Date")
    message = fields.Char(string="Message")
