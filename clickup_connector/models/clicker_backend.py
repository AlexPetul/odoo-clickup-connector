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

    def _fetch_lists(self, request_manager, space_id):
        response, status = request_manager.get_lists_by_space_id(space_id)
        if status == 200:
            return response.get("lists", [])

    def _fetch_folder_lists(self, request_manager, space_id, clicker_space_id):
        lists = list()
        response, status = request_manager.get_folders_by_space_id(clicker_space_id)
        if status == 200:
            folders = response.get("folders", [])
            space_id.folders_count = len(folders)
            for folder in folders:
                response, status = request_manager.get_lists_by_folder_id(folder["id"])
                if status == 200:
                    lists.append(response.get("lists"))
        return lists

    def activate(self):
        request_manager = RequestsManager(self.env, self.token)
        response, status = request_manager.get_teams()
        if status == 200:
            for team in response.get("teams", []):
                response, status = request_manager.get_spaces_by_team_id(team["id"])
                for space in response.get("spaces", []):
                    folder_lists = self._fetch_folder_lists(request_manager, space_id, space["id"])
                    raw_lists = self._fetch_lists(request_manager, space["id"])
                    clicker_lists = folder_lists + raw_lists

                    space_id = self.env["clicker.space"].create({
                        "name": space["name"],
                        "clicker_backend_id": self.id,
                        "clicker_id": space["id"]
                    })

                    self.state = "running"

    def reset(self):
        self.state = "authenticate"
