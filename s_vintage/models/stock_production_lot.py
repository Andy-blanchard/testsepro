# -*- coding: utf-8 -*-

from odoo import fields, models

class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    ref = fields.Char('Vintage', help="Internal reference number in case it differs from the manufacturer's lot/serial number")
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    s_vin = fields.Selection([('vin', 'Wine'), ('no_vin', 'No Wine')], string="Wine")
    
