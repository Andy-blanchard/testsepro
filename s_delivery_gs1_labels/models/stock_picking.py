# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def on_barcode_scanned(self, barcode):
        if not self.env.company.nomenclature_id:
            # Logic for products
            product = self.env['product.product'].search(['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)
            if product:
                if self._check_product(product):
                    return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id,product_packaging.qty):
                    return

            # Logic for packages in source location
            if self.move_line_ids:
                package_source = self.env['stock.quant.package'].search([('name', '=', barcode), ('location_id', 'child_of', self.location_id.id)], limit=1)
                if package_source:
                    if self._check_source_package(package_source):
                        return

            # Logic for packages in destination location
            package = self.env['stock.quant.package'].search([('name', '=', barcode), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
            if package:
                if self._check_destination_package(package):
                    return

            # Logic only for destination location
            location = self.env['stock.location'].search(['|', ('name', '=', barcode), ('barcode', '=', barcode)], limit=1)
            if location and location.search_count([('id', '=', location.id), ('id', 'child_of', self.location_dest_id.ids)]):
                if self._check_destination_location(location):
                    return
        else:
            parsed_result = self.env.company.nomenclature_id.parse_barcode(barcode)
            if parsed_result['type'] in ['weight', 'product']:
                if parsed_result['type'] == 'weight':
                    product_barcode = parsed_result['base_code']
                    qty = parsed_result['value']
                else: #product
                    product_barcode = parsed_result['code']
                    qty = 1.0
                    lot_id = False
                    if parsed_result['encoding'] == 'gs1':
                        qty = parsed_result['quantity'] if parsed_result['quantity'] else 1.0
                        product = self.env['product.product'].search(['|', ('barcode', '=', product_barcode), ('default_code', '=', product_barcode)], limit=1)
                        if product and parsed_result['lot']:
                            lot_id = self.env['stock.production.lot'].search([('name', '=', parsed_result['lot']), ('product_id', '=', product.id)], limit=1)
                product = self.env['product.product'].search(['|', ('barcode', '=', product_barcode), ('default_code', '=', product_barcode)], limit=1)
                if product:
                    if parsed_result['encoding'] == 'gs1':
                        if self.with_context(gs1=1)._check_product(product, qty, lot_id):
                            return                        
                    else:
                        if self._check_product(product, qty, lot_id):
                            return

            if parsed_result['type'] == 'package':
                if self.move_line_ids:
                    package_source = self.env['stock.quant.package']
                    if parsed_result['encoding'] == 'gs1':
                        package_source = self.env['stock.quant.package'].search([('sscc_number', '=', parsed_result['code']), ('location_id', 'child_of', self.location_id.id)], limit=1)
                    else:
                        package_source = self.env['stock.quant.package'].search([('name', '=', parsed_result['code']), ('location_id', 'child_of', self.location_id.id)], limit=1)
                    if package_source:
                        if self._check_source_package(package_source):
                            return
                
                package = self.env['stock.quant.package']
                if parsed_result['encoding'] == 'gs1':
                    package = self.env['stock.quant.package'].search([('sscc_number', '=', parsed_result['code']), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
                    if not package:
                        package = self.env['stock.quant.package'].search([('sscc_number', '=', parsed_result['code'])], limit=1)                        
                else:  
                    package = self.env['stock.quant.package'].search([('name', '=', parsed_result['code']), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
                if package:
                    if parsed_result['encoding'] == 'gs1':
                        if self.with_context(gs1=1)._check_destination_package(package):
                            return
                    else:
                        if self._check_destination_package(package):
                            return

            if parsed_result['type'] == 'location':
                location = self.env['stock.location'].search(['|', ('name', '=', parsed_result['code']), ('barcode', '=', parsed_result['code'])], limit=1)
                if location and location.search_count([('id', '=', location.id), ('id', 'child_of', self.location_dest_id.ids)]):
                    if self._check_destination_location(location):
                        return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', parsed_result['code'])], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id,product_packaging.qty):
                    return

        return {'warning': {
            'title': _('Wrong barcode'),
            'message': _('The barcode "%(barcode)s" doesn\'t correspond to a proper product, package or location.') % {'barcode': barcode}
        }}
    
    def _check_product(self, product, qty=1.0, lot_id=False):
        if self._context.get('gs1'):   
            picking_move_lines = self.move_line_ids_without_package            
    
            corresponding_ml = picking_move_lines
    
            if corresponding_ml:
                corresponding_ml.qty_done += float(qty)
                corresponding_ml.lot_id = lot_id.id
            else:
                # If a candidate is not found, we create one here. If the move
                # line we add here is linked to a tracked product, we don't
                # set a `qty_done`: a next scan of this product will open the
                # lots wizard.
                picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
                new_move_line = self.move_line_ids.new({
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'qty_done':  qty or 0.0,
                    'product_uom_qty': 0.0,
                    'date': fields.datetime.now(),
                    'lot_id': lot_id.id
                })
                
                self.move_line_ids_without_package += new_move_line
            return True
        else:
            return super(StockPicking, self)._check_product(product, qty, lot_id)
    
    def _check_destination_package(self, package):
        if self._context.get('gs1'):
            corresponding_ml = self.move_line_ids_without_package            
            for ml in corresponding_ml:
                rounding = ml.product_uom_id.rounding
                if float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) == -1:
                    self += self.new({
                        'product_id': ml.product_id.id,
                        'package_id': ml.package_id.id,
                        'product_uom_id': ml.product_uom_id.id,
                        'location_id': ml.location_id.id,
                        'location_dest_id': ml.location_dest_id.id,
                        'qty_done': 0.0,
                        'move_id': ml.move_id.id,
                        'date': fields.datetime.now(),
                        'result_package_id':  package.id
                    })
                if not ml.result_package_id:
                    ml.result_package_id = package.id
            return True
        else:
            return super(StockPicking, self)._check_destination_package(package)
        
        
        
    
    
