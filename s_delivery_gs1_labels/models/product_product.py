# -*- coding: utf-8 -*-

from odoo import api, fields, SUPERUSER_ID, http, models, _
from odoo.exceptions import UserError

from ..common import get_gs1_barcode
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def create_barcode_number(self):
        for prod in self:
            if prod.barcode and len(prod.barcode) > 0:
                raise UserError(_('Product %s already has an assigned barcode [%s]. If you are sure, you want to set a new barcode, please empty the current barcode field.') % (prod.display_name, prod.barcode))

            generated_barcode = get_gs1_barcode(self.env)
            if generated_barcode:
                prod.barcode = generated_barcode
                
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        domain = []
        if name and ('(01)' in str(name) or '(02)' in str(name)):
            barcode = str(name)
            index_product = barcode.find('(01)')
            if index_product == -1:
                index_product = barcode.find('(02)')
            
            
            product_code = barcode[index_product+5:]
            if '(' in product_code:
                index_new_bracket = product_code.find('(')
                product_code = product_code[:index_new_bracket]            
            if not product_code:
                product_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
            else:
                product_ids = self._search([('barcode', '=', product_code)], limit=limit, access_rights_uid=name_get_uid)
            return models.lazy_name_get(self.browse(product_ids).with_user(name_get_uid))
            
        else:
            return super(ProductProduct, self)._name_search(name, args, operator, limit, name_get_uid)
            
          

