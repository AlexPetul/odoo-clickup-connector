from itertools import chain
from odoo import _, api, fields, models

from ..clickup.requests_manager import RequestsManager


class ClickerBackend(models.Model):
    _name = "clicker.backend"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Clickup model to provide authentication backends"

    name = fields.Char(string="Name")
    uri = fields.Char(string="ClickUp URI", required=True)
    token = fields.Char(string="API Token", copy=False)
    oauth_token = fields.Char(string="Oauth Token", copy=False)
    state = fields.Selection(selection=[("authenticate", "Authenticate"), ("setup", "Setup"), ("running", "Running")],
                             default="authenticate", required=True, readonly=True)
    member_ids = fields.Many2many(comodel_name="res.users", copy=False)
    member_ids_count = fields.Integer(compute="_compute_member_ids_count")
    space_ids = fields.One2many(comodel_name="clicker.space", inverse_name="clicker_backend_id", string="Spaces", copy=False)
    space_ids_count = fields.Integer(compute="_compute_space_ids_count")

    @api.depends("member_ids")
    def _compute_member_ids_count(self) -> None:
        for record in self:
            record.member_ids_count = len(record.member_ids)

    @api.depends("space_ids")
    def _compute_space_ids_count(self) -> None:
        for record in self:
            record.space_ids_count = len(record.space_ids)

    def get_members(self):
        request_manager = RequestsManager(self.env, self.token or self.oauth_token)
        response, status = request_manager.get_teams()
        if status == 200 and response.get("teams", []):
            return [x["members"] for x in response["teams"]]

    def import_members(self) -> None:
        for member in list(chain.from_iterable(self.get_members())):
            user_id = self.env["clicker.space"].get_user_by_username_or_email(member["user"])
            if not user_id:
                user_id = self.env["res.users"].create({
                    "name": member["user"]["username"],
                    "login": member["user"]["email"]
                }).id
            self.member_ids = [(4, user_id)]

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

    def action_open_space_ids(self) -> dict:
        return {
            "name": _("Spaces"),
            "type": "ir.actions.act_window",
            "view_mode": "kanban,form,tree",
            "res_model": "clicker.space",
            "target": "current",
            "domain": [("clicker_backend_id", "=", self.id)]
        }

    def action_open_member_ids(self) -> dict:
        return {
            "name": _("Users"),
            "type": "ir.actions.act_window",
            "view_mode": "tree,kanban,form",
            "res_model": "res.users",
            "target": "current",
            "domain": [("id", "in", self.member_ids.ids)]
        }
