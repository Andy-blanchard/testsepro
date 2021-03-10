# -*- coding: utf-8 -*-

from odoo import models,fields, _
from odoo.exceptions import UserError



class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'
    
    def open_produce_product(self):
        self.ensure_one()
        if self.bom_id.type == 'phantom':
            raise UserError(_('You cannot produce a MO with a bom kit product.'))
        action = self.env.ref('mrp.act_mrp_product_produce').read()[0]
        action['context'] = {'default_s_manufactoring_order': self.name}
        return action
    
    def button_mark_done(self):
        self.ensure_one()
        self._check_company()
        for wo in self.workorder_ids:
            if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
                raise UserError(_('Work order %s is still running') % wo.name)
        self._check_lots()

        self.post_inventory()
        # Moves without quantity done are not posted => set them as done instead of canceling. In
        # case the user edits the MO later on and sets some consumed quantity on those, we do not
        # want the move lines to be canceled.
        (self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
            'state': 'done',
            'product_uom_qty': 0.0,
        })
        if self.move_raw_ids:
            s_mel = []
            for s_product_id in self.move_raw_ids:
                if s_product_id.product_id.s_vin == 'vin':
                    for s_move_line_id in s_product_id.move_line_ids:
                        s_ref = s_move_line_id.lot_id.ref
                        s_mel.append(s_ref)
        if self.finished_move_line_ids:
            for s_finished__product in self.finished_move_line_ids:
                if s_mel:
                    s_mel_not_null = []
                    for s_mel_not_false in s_mel:
                        if s_mel_not_false:
                            s_mel_not_null.append(s_mel_not_false)
                    if s_mel_not_null:
                        s_finished__product.lot_id.write({'ref': s_mel_not_null[0]})

        return self.write({'date_finished': fields.Datetime.now()})
        
