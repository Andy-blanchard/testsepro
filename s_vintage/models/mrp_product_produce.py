# -*- coding: utf-8 -*-

from odoo import fields, models, _


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"
    
    
    s_manufactoring_order = fields.Char('name')
    
    def action_generate_serial(self):
        self.ensure_one()
        product_produce_wiz = self.env.ref('mrp.view_mrp_product_produce_wizard', False)
        self.finished_lot_id = self.env['stock.production.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.production_id.company_id.id,
            'name': self.production_id.name,
        })
        return {
            'name': _('Produce'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mrp.product.produce',
            'res_id': self.id,
            'view_id': product_produce_wiz.id,
            'target': 'new',
        }
    
    
    