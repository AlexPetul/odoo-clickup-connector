import requests

from odoo import http
from odoo.http import request


class OAuthRedirectController(http.Controller):

    @http.route(["/oauth/"], type="http", auth="public", website=False)
    def handle_redirect(self, *args, **kwargs):
        print(kwargs, request.__dict__)
        requests.get(f'https://api.clickup.com/api/v2/oauth/token?client_id={kwargs.get("client_id")}&client_secret=M9DK7R826MTJL60EQOLHSU3LXWD8X6OBQYZT409T2EM6NXAFGH37DPAJYLBA5ZNZ&code={kwargs.get("code")}')
        return None
