from odoo import fields, models, _
from odoo.exceptions import UserError

from ..clickup.requests_manager import RequestsManager


class ClickerBackendAuth(models.TransientModel):
    _name = "clicker.backend.auth"

    method = fields.Selection(selection=[("oauth", "OAuth 2.0"), ("token", "API Token")], default="oauth", required=True)
    token = fields.Char(string="API Token")
    client_id = fields.Char(string="Client ID")
    client_secret = fields.Char(string="Client Secret")

    def authenticate_with_token(self) -> None:
        request_manager = RequestsManager(self.env, self.token)
        response, status_code = request_manager.get_teams()
        if status_code == 200:
            self.env["clicker.backend"].browse(self.env.context.get("active_id")).write({
                "token": self.token,
                "state": "setup"
            })
        else:
            raise UserError(_("An error occurred while trying to execute request, please check credentials."))
