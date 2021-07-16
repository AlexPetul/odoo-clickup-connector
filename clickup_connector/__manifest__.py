{
    "name": "ClickUp Connector",
    "version": "1.0",
    "category": "Tools",
    "summary": "Base utils.",
    "description": """
               Clickup Odoo Connector.
    """,
    "depends": [
        "base",
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        'wizards/clicker_backend_auth_wizard.xml',
        "views/assets.xml",
        "views/clicker_backend_views.xml",
        "views/clicker_spaces_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/clicker_backend_demo.xml",
    ],
    "qweb": [
        "static/src/xml/tasks_hierarchy_templates.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}
