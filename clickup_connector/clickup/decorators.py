from typing import Callable
from functools import wraps

from odoo import api, SUPERUSER_ID
from odoo.tools import config
from odoo.modules.registry import Registry


def api_method(func: Callable):
    @wraps(func)
    def closure(*args, **kwargs):
        try:
            db_registry = Registry.new(db_name=kwargs.get("db_name"))
        except (IndexError, Exception):
            db_registry = Registry.new(db_name=config["db_name"])

        with api.Environment.manage(), db_registry.cursor() as cr:
            args[0].env = api.Environment(cr=cr, uid=SUPERUSER_ID, context={})
            return func(*args, **kwargs)
    return closure
