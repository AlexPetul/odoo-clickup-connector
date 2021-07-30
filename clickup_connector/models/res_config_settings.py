from odoo import api, fields, models

from ..models import constants as const


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_clicker = fields.Boolean(string="ClickUp Management", config_parameter="clickup_connector.module_clicker", implied_group="clickup_connector.group_project_click_up_management")
    clicker_api_uri = fields.Char(string="API URI", config_parameter="clickup_connector.clicker_api_uri")
    enable_webhooks = fields.Boolean(default=False, string="Enable Webhooks", config_parameter="clickup_connector.enable_webhooks")

    @api.model
    def get_values(self) -> dict:
        res = super(ResConfigSettings, self).get_values()

        ir_config = self.env["ir.config_parameter"].sudo()
        clicker_api_uri = ir_config.get_param("clicker_api_uri", default="https://api.clickup.com/api/v2/")
        module_clicker = ir_config.get_param("module_clicker", default=False)
        enable_webhooks = ir_config.get_param("enable_webhooks", default=True)

        res.update({
            "clicker_api_uri": clicker_api_uri,
            "module_clicker": module_clicker,
            "enable_webhooks": enable_webhooks
        })

        return res

    def set_values(self) -> None:
        super(ResConfigSettings, self).set_values()

        ir_config = self.env["ir.config_parameter"].sudo()

        if self.clicker_api_uri and not self.clicker_api_uri.endswith("/"):
            self.clicker_api_uri += "/"

        ir_config.set_param("clicker_api_uri", self.clicker_api_uri or const.DEFAULT_CLICKUP_API_URL)
        ir_config.set_param("module_clicker", self.module_clicker)
        ir_config.set_param("enable_webhooks", self.enable_webhooks)

        group_id = self.env["res.groups"].browse(self.env.ref("clickup_connector.group_project_click_up_management").id)
        group_id.users = [(4 if self.module_clicker else 3, self.env.user.id)]
