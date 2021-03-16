# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_round

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'  
    
    qty_done_char = fields.Char(string='Done', default=0.0, digits='Product Unit of Measure', copy=False)  
    scan_qty = fields.Boolean(string="Scan Quantity") 
    
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
                    if self._check_product(product, qty, lot_id):
                        return

            if parsed_result['type'] == 'package':
                if self:
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
                else:  
                    package = self.env['stock.quant.package'].search([('name', '=', parsed_result['code']), '|', ('location_id', '=', False), ('location_id','child_of', self.location_dest_id.id)], limit=1)
                if package:
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
        """ This method is called when the user scans a product. Its goal
        is to find a candidate move line (or create one, if necessary)
        and process it by incrementing its `qty_done` field with the
        `qty` parameter.
        """
        # Get back the move line to increase. If multiple are found, chose
        # arbitrary the first one. Filter out the ones processed by
        # `_check_location` and the ones already having a # destination
        # package.
        #picking_move_lines = self.move_line_ids_without_package
        #if not self.show_reserved:
        picking_move_lines = self

        corresponding_ml = picking_move_lines#.filtered(lambda ml: ml.product_id.id == product.id and not ml.result_package_id and not ml.location_processed and not ml.lots_visible)[:1]

        if corresponding_ml:
            corresponding_ml.qty_done += float(qty)
            corresponding_ml.lot_id = lot_id.id
        else:
            # If a candidate is not found, we create one here. If the move
            # line we add here is linked to a tracked product, we don't
            # set a `qty_done`: a next scan of this product will open the
            # lots wizard.
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            new_move_line = self.new({
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'qty_done':  qty or 0.0,
                'product_uom_qty': 0.0,
                'date': fields.datetime.now(),
                'lot_id': lot_id.id
            })
            
            self += new_move_line
        return True
    
    
    def _check_source_package(self, package):
        corresponding_po = self
        for po in corresponding_po:
            po.qty_done = po.product_uom_qty
        if corresponding_po:
            self.entire_package_detail_ids.filtered(lambda p: p.name == package.name).is_processed = True
            return True
        else:
            return False

    def _check_destination_package(self, package):
        """ This method is called when the user scans a package currently
        located in (or in any of the children of) the destination location
        of the picking. Its goal is to set this package as a destination
        package for all the processed move lines not having a destination
        package.
        """
        corresponding_ml = self
        # If the user processed the whole reservation (or more), simply
        # write the `package_id` field.
        # If the user processed less than the reservation, split the
        # concerned move line in two: one where the `package_id` field
        # is set with the processed quantity as `qty_done` and another
        # one with the initial values.
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
            ml.result_package_id = package.id
        return True

    def _check_destination_location(self, location):
        """ This method is called when the user scans a location. Its goal
        is to find the move lines previously processed and write the scanned
        location as their `location_dest_id` field.
        """
        # Get back the move lines the user processed. Filter out the ones where
        # this method was already applied thanks to `location_processed`.
        corresponding_ml = self

        # If the user processed the whole reservation (or more), simply
        # write the `location_dest_id` and `location_processed` fields
        # on the concerned move line.
        # If the user processed less than the reservation, split the
        # concerned move line in two: one where the `location_dest_id`
        # and `location_processed` fields are set with the processed
        # quantity as `qty_done` and another one with the initial values.
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
                })
            ml.update({
                'location_processed': True,
                'location_dest_id': location.id,
            })
        return True
    
    @api.onchange('qty_done_char')
    def _onchange_qty_done_char(self):
        if self.qty_done_char and '(37)' in str(self.qty_done_char):
            quantity = False
            barcode = str(self.qty_done_char)
            index_37 = barcode.find('(37)')
            quantity = barcode[index_37+4:]
            if '(' in quantity:
                index_new_bracket = quantity.find('(')
                quantity = quantity[:index_new_bracket]
            self.qty_done_char = quantity
            self.qty_done = quantity
        else:
            try:                
                self.qty_done = float(self.qty_done_char)
            except:
                self.qty_done = 0.0
                self.qty_done_char = 0.0
            
    @api.onchange('qty_done')
    def _onchange_qty_done(self):
        res = super(StockMoveLine, self)._onchange_qty_done()
        if self.qty_done and float_compare(self.qty_done, float(self.qty_done_char), precision_rounding=self.product_uom_id.rounding) != 0:
            self.qty_done_char = self.qty_done
        return res
                
    