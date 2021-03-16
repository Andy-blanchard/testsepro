# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    _order = 'id desc'
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        serial_lot = False
        if name and '(10)' in str(name):
            barcode = str(name)
            index_10 = barcode.find('(10)')
            serial_lot = barcode[index_10+4:]
            if '(' in serial_lot:
                index_new_bracket = serial_lot.find('(')
                serial_lot = serial_lot[:index_new_bracket]                         
        if not serial_lot:
            lot_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        else:
            lot_ids = self._search([('name', '=', serial_lot)], limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(lot_ids).with_user(name_get_uid))
    