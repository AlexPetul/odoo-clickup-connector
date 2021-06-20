import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from ..service.requests_manager import RequestsManager


class ClickerBackendAuth(models.TransientModel):
    _name = "clicker.backend.auth"

    method = fields.Selection(selection=[("oauth", "OAuth 2.0"), ("token", "API Token")], default="oauth", required=True)
    token = fields.Char(string="API Token")
    client_id = fields.Char(string="Client ID")
    secret_key = fields.Char(string="Client Secret")

    def authenticate_with_token(self):
        api_uri = self.env["ir.config_parameter"].sudo().get_param('clickup_connector.clicker_api_uri')
        if api_uri:
            response, status_code = RequestsManager.execute_get(api_uri, "team", token=self.token)
            if status_code == 200:
                self.env["clicker.backend"].browse(self.env.context.get("active_id")).write({
                    "token": self.token,
                    "state": "setup"
                })
            else:
                raise UserError(_("An error occurred while trying to execute request, please check credentials."))
        else:
            raise UserError(_("Please provide ClickUp API URI in project settings."))
