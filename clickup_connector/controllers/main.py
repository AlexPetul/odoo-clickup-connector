from odoo import http
from odoo.http import request

from ..service.requests_manager import RequestsManager


class OAuthRedirectController(http.Controller):

    @http.route(["/oauth/<int:model_id>/<string:client_id>/<string:key>/"], type="http", auth="public", website=False)
    def handle_redirect(self, *args, **kwargs):
        request_manager = RequestsManager(request.env)
        model_id, client_id, key = tuple(request.endpoint_arguments.values())
        response, status = request_manager.get_access_token(
            {"client_id": client_id, "client_secret": key, "code": kwargs.get("code")}
        )

        if status == 200:
            request.env["clicker.backend"].browse(model_id).write({
                "oauth_token": response.get("access_token"),
                "state": "setup"
            })
            return http.redirect_with_hash("/")
