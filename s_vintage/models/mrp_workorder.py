# -*- coding: utf-8 -*-
from odoo import fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    
    def s_compute_pending_production(self):
        self.s_manufactoring_order = self.production_id.name
    
    s_manufactoring_order = fields.Char('name', compute='s_compute_pending_production')
    
    def action_generate_serial(self):
        self.ensure_one()
        self.finished_lot_id = self.env['stock.production.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'name': self.production_id.name,
        })