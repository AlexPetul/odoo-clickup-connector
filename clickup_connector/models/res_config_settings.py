from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    module_clicker = fields.Boolean(string="ClickUp Management", config_parameter="clickup_connector.module_clicker")
    clicker_api_uri = fields.Char(string="API URI", config_parameter="clickup_connector.clicker_api_uri")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        ir_config = self.env["ir.config_parameter"].sudo()
        clicker_api_uri = ir_config.get_param("clicker_api_uri", default="https://api.clickup.com/api/v2/")
        module_clicker = ir_config.get_param("module_clicker", default=False)

        res.update({
            "clicker_api_uri": clicker_api_uri,
            "module_clicker": module_clicker
        })

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        ir_config = self.env["ir.config_parameter"].sudo()
        if not self.clicker_api_uri.endswith("/"):
            self.clicker_api_uri += "/"
        ir_config.set_param("clicker_api_uri", self.clicker_api_uri or "https://api.clickup.com/api/v2/")
        ir_config.set_param("module_clicker", self.module_clicker)
