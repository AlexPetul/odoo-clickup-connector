from odoo import api, fields, models, _
from odoo.exceptions import UserError
import webbrowser

from ..service.requests_manager import RequestsManager


class ClickerBackendAuth(models.TransientModel):
    _name = "clicker.backend.auth"

    method = fields.Selection(selection=[("oauth", "OAuth 2.0"), ("token", "API Token")], default="oauth", required=True)
    token = fields.Char(string="API Token")
    client_id = fields.Text(string="Client ID")
    secret_key = fields.Char(string="Client Secret")

    def authenticate_with_oauth(self):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36"}
        oauth_uri = f'https://app.clickup.com/api?client_id={self.client_id}&redirect_uri=https://localhost:8069/web'

    def authenticate_with_token(self):
        request_manager = RequestsManager(self.env, self.token)
        response, status_code = request_manager.get_teams()
        if status_code == 200:
            self.env["clicker.backend"].browse(self.env.context.get("active_id")).write({
                "token": self.token,
                "state": "setup"
            })
        else:
            raise UserError(_("An error occurred while trying to execute request, please check credentials."))
