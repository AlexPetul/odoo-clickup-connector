from odoo import _, api, fields, models

from ..clickup.requests_manager import RequestsManager


class ClickerBackend(models.Model):
    _name = "clicker.backend"

    name = fields.Char(string="Name")
    uri = fields.Char(string="ClickUp URI", required=True)
    token = fields.Char(string="API Token", copy=False)
    oauth_token = fields.Char(string="Oauth Token", copy=False)
    state = fields.Selection(selection=[("authenticate", "Authenticate"), ("setup", "Setup"), ("running", "Running")],
                             default="authenticate", required=True, readonly=True)
    space_ids = fields.One2many(comodel_name="clicker.space", inverse_name="clicker_backend_id", string="Spaces",
                                copy=False)
    space_ids_count = fields.Integer(compute="_compute_space_ids_count")

    @api.depends("space_ids")
    def _compute_space_ids_count(self) -> None:
        for record in self:
            record.space_ids_count = len(record.space_ids)

    def action_open_space_ids(self) -> dict:
        return {
            "name": _("Spaces"),
            "type": "ir.actions.act_window",
            "view_mode": "kanban,form,tree",
            "res_model": "clicker.space",
            "target": "current",
            "domain": [("clicker_backend_id", "=", self.id)]
        }

    def activate(self) -> None:
        request_manager = RequestsManager(self.env, self.token or self.oauth_token)
        response, status = request_manager.get_teams()
        if status == 200:
            for team in response.get("teams", []):
                response, status = request_manager.get_spaces_by_team_id(team["id"])
                for space in response.get("spaces", []):
                    self.env["clicker.space"].create({
                        "name": space["name"],
                        "clicker_backend_id": self.id,
                        "team_id": team["id"],
                        "clicker_id": space["id"],
                        "is_private": space["private"]
                    })

                    self.write({"state": "running"})

    def reset(self) -> None:
        self.write({"state": "authenticate"})
