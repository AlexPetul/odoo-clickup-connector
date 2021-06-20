from odoo import api, fields, models, _

from ..service.requests_manager import RequestsManager


class ClickerBackend(models.Model):
    _name = "clicker.backend"

    name = fields.Char(string="Name")
    uri = fields.Char(string="ClickUp URI", required=True)
    token = fields.Char(string="API Token")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company
    )
    state = fields.Selection(
        selection=[
            ("authenticate", "Authenticate"),
            ("setup", "Setup"),
            ("running", "Running"),
        ],
        default="authenticate",
        required=True,
        readonly=True
    )
    space_ids = fields.One2many(
        comodel_name="clicker.space",
        inverse_name="clicker_backend_id",
        string="Spaces",
        copy=False
    )
    space_ids_count = fields.Integer(compute="_compute_space_ids_count")

    @api.depends("space_ids")
    def _compute_space_ids_count(self):
        for record in self:
            record.space_ids_count = len(record.space_ids)

    def action_open_space_ids(self):
        return {
            "name": _("Spaces"),
            "type": "ir.actions.act_window",
            "view_mode": "kanban,form,tree",
            "res_model": "clicker.space",
            "target": "current",
            "domain": [("clicker_backend_id", "=", self.id)]
        }

    def activate(self):
        api_uri = self.env["ir.config_parameter"].sudo().get_param('clickup_connector.clicker_api_uri')
        response, status = RequestsManager.execute_get(api_uri, "team", token=self.token)
        if status == 200:
            for team in response.get("teams", []):
                response, status = RequestsManager.execute_get(api_uri, f'team/{team["id"]}/space', token=self.token)
                for space in response.get("spaces", []):
                    if not space["id"] in self.space_ids.mapped("clicker_id"):
                        self.env["clicker.space"].create({
                            "name": space["name"],
                            "clicker_backend_id": self.id,
                            "clicker_id": space["id"],
                        })
                        print(RequestsManager.execute_get(api_uri, f'space/{space["id"]}/list', token=self.token))
                        self.state = "running"

    def reset(self):
        self.state = "authenticate"
