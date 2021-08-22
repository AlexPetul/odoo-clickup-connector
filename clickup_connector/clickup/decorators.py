from functools import wraps

from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry


def api_method(func):
    @wraps(func)
    def closure(*args, **kwargs):
        db_registry = Registry.new(db_name=args[2])
        with api.Environment.manage(), db_registry.cursor() as cr:
            args[0].env = api.Environment(cr=cr, uid=SUPERUSER_ID, context={})
            return func(*args, **kwargs)
    return closure
