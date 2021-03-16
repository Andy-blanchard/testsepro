# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

from ..common import calculate_gs1_check_digit, GTIN_LENGTH, GTIN_14_LENGTH, GLN_LENGTH, SSCC_LENGTH, SSCC_EXTENSION_DIGIT

_logger = logging.getLogger(__name__)
from odoo.osv import expression


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    computed_barcode_article_text = fields.Char('GS1 Article Barcode Text', compute='_compute_barcode_article_text', index=False,
                                           readonly=True, compute_sudo=True, store=False)
    computed_barcode_lot_text = fields.Char('GS1 Lot Barcode Text', compute='_compute_barcode_lot_text', index=False, readonly=True,
                                       compute_sudo=True, store=False)

    computed_barcode_article = fields.Char('GS1 Article Barcode', compute='_compute_barcode_article', index=False,
                                           readonly=True, compute_sudo=True, store=False)
    computed_barcode_lot = fields.Char('GS1 Lot Barcode', compute='_compute_barcode_lot', index=False, readonly=True,
                                       compute_sudo=True, store=False)

    @api.depends('computed_barcode_article_text')
    def _compute_barcode_article(self):
        for stock_quant in self:
            stock_quant.computed_barcode_article = stock_quant.computed_barcode_article_text\
                .replace('(', '').replace(')', '')

    @api.depends('computed_barcode_lot_text')
    def _compute_barcode_lot(self):
        for stock_quant in self:
            stock_quant.computed_barcode_lot = stock_quant.computed_barcode_lot_text \
                .replace('(', '').replace(')', '')

    @api.depends('quantity', 'product_id')
    def _compute_barcode_article_text(self):
        for stock_quant in self:
            return_str = ''
            if stock_quant.product_id.barcode and len(stock_quant.product_id.barcode) == GTIN_LENGTH:
                return_str += '(02)0%s' % stock_quant.product_id.barcode
            elif stock_quant.product_id.barcode and len(stock_quant.product_id.barcode) == GTIN_14_LENGTH:
                return_str += '(02)%s' % stock_quant.product_id.barcode

            if stock_quant.product_id.tracking != 'none' and stock_quant.lot_id and stock_quant.lot_id.use_date:
                return_str += '(15)%s' % stock_quant.lot_id.use_date.strftime('%y%m%d')

            return_str += '(37)%s' % int(stock_quant.quantity)

            if stock_quant.product_id.tracking != 'none' and stock_quant.lot_id:
                return_str += '(10)%s' % stock_quant.lot_id.name

            stock_quant.computed_barcode_article_text = return_str

    @api.depends('package_id', 'product_id')
    def _compute_barcode_lot_text(self):
        for stock_quant in self:
            return_str = ''

            if stock_quant.package_id and len(stock_quant.package_id) > 0 and stock_quant.package_id[0].sscc_number:
                return_str += '(00)%s' % stock_quant.package_id[0].sscc_number

            stock_quant.computed_barcode_lot_text = return_str


class QuantPackage(models.Model):
    """ Packages containing quants and/or other packages """
    _inherit = "stock.quant.package"

    sscc_number = fields.Char('SSCC', compute='_compute_sscc_number', index=True, compute_sudo=True, store=True)

    @api.depends('quant_ids', 'quant_ids.product_id', 'quant_ids.product_id.barcode')
    def _compute_sscc_number(self):
        for quant in self:
            if quant.sscc_number and len(quant.sscc_number) == SSCC_LENGTH:
                continue

            if not quant.quant_ids:
                quant.sscc_number = False
                continue

            if not quant.quant_ids[0].product_id:
                quant.sscc_number = False
                continue

            if not quant.quant_ids[0].product_id[0].barcode or len(quant.quant_ids[0].product_id[0].barcode) != GTIN_LENGTH:
                quant.sscc_number = False
                continue

            gs1_base = quant.quant_ids[0].product_id[0].barcode[:9]
            if not gs1_base or len(gs1_base) != GLN_LENGTH:
                quant.sscc_number = False
                continue

            serial = self.env['ir.sequence'].next_by_code('s.gs1.sscc.number') or '0000000'
            temp_sscc = '%s%s%s' % (SSCC_EXTENSION_DIGIT, gs1_base, serial)

            quant.sscc_number = '%s%s' % (temp_sscc, calculate_gs1_check_digit(temp_sscc))
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        sscc_code = False
        print(name)
        if name and '(00)' in str(name):
            barcode = str(name)
            index_00 = barcode.find('(00)')
            sscc_code = barcode[index_00+4:]
            if '(' in sscc_code:
                index_new_bracket = sscc_code.find('(')
                sscc_code = sscc_code[:index_new_bracket]                         
        if not sscc_code:
            stock_quant_package_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        else:            
            stock_quant_package_ids = self._search([('sscc_number', '=', sscc_code)], limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(stock_quant_package_ids).with_user(name_get_uid))
    
    
    
    
    
    
    
    
    
    
    
    