# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import re

class BarcodeRule(models.Model):
    _inherit = 'barcode.rule'
    
    encoding = fields.Selection(selection_add=[('gs1', 'GS1')])
    
class BarcodeNomenclature(models.Model):
    _inherit = 'barcode.nomenclature'
    
    # Attempts to interpret an barcode (string encoding a barcode)
    # It will return an object containing various information about the barcode.
    # most importantly : 
    #  - code    : the barcode
    #  - type   : the type of the barcode: 
    #  - value  : if the id encodes a numerical value, it will be put there
    #  - base_code : the barcode code with all the encoding parts set to zero; the one put on
    #                the product in the backend
    def parse_barcode(self, barcode):
        parsed_result = {
            'encoding': '', 
            'type': 'error', 
            'code': barcode, 
            'base_code': barcode, 
            'value': 0,
            'lot': False,
            'quantity': False
        }

        rules = []
        for rule in self.rule_ids:
            rules.append({'type': rule.type, 'encoding': rule.encoding, 'sequence': rule.sequence, 'pattern': rule.pattern, 'alias': rule.alias})

        for rule in rules:
            cur_barcode = barcode
            if rule['encoding'] == 'ean13' and self.check_encoding(barcode,'upca') and self.upc_ean_conv in ['upc2ean','always']:
                cur_barcode = '0'+cur_barcode
            elif rule['encoding'] == 'upca' and self.check_encoding(barcode,'ean13') and barcode[0] == '0' and self.upc_ean_conv in ['ean2upc','always']:
                cur_barcode = cur_barcode[1:]
            elif rule['encoding'] == 'gs1' and rule['type'] == 'package' and self.check_encoding(barcode, 'gs1') and '(00)' in barcode :
                cur_barcode = self.get_sscc(barcode)
                parsed_result['encoding'] = rule['encoding']
                parsed_result['type'] = rule['type']
                parsed_result['code'] = cur_barcode
                parsed_result['base_code'] = cur_barcode
                break
            elif rule['encoding'] == 'gs1' and rule['type'] == 'product' and self.check_encoding(barcode, 'gs1') and ('(01)' in barcode or '(02)' in barcode):
                cur_barcode = self.get_product_code(barcode)
                parsed_result['encoding'] = rule['encoding']
                parsed_result['type'] = rule['type']
                parsed_result['code'] = cur_barcode
                parsed_result['base_code'] = cur_barcode
                parsed_result['lot'] = self.get_serial_lot(barcode)
                parsed_result['quantity'] = self.get_quantity(barcode)
                break
            if not self.check_encoding(barcode,rule['encoding']):
                continue
            
            
                
                
                    
            if not rule['encoding'] == 'gs1':
                match = self.match_pattern(cur_barcode, rule['pattern'])
                if match['match']:
                    if rule['type'] == 'alias':
                        barcode = rule['alias']
                        parsed_result['code'] = barcode
                    else:
                        parsed_result['encoding'] = rule['encoding']
                        parsed_result['type'] = rule['type']
                        parsed_result['value'] = match['value']
                        parsed_result['code'] = cur_barcode
                        if rule['encoding'] == "ean13":
                            parsed_result['base_code'] = self.sanitize_ean(match['base_code'])
                        elif rule['encoding'] == "upca":
                            parsed_result['base_code'] = self.sanitize_upc(match['base_code'])
                        else:
                            parsed_result['base_code'] = match['base_code']
                        return parsed_result

        return parsed_result
    
     # returns true if the barcode string is encoded with the provided encoding.
    def check_encoding(self, barcode, encoding):
        if encoding == 'ean13':
            return len(barcode) == 13 and re.match("^\d+$", barcode) and self.ean_checksum(barcode) == int(barcode[-1]) 
        elif encoding == 'ean8':
            return len(barcode) == 8 and re.match("^\d+$", barcode) and self.ean8_checksum(barcode) == int(barcode[-1])
        elif encoding == 'upca':
            return len(barcode) == 12 and re.match("^\d+$", barcode) and self.ean_checksum("0"+barcode) == int(barcode[-1])
        elif encoding == 'gs1':
            return self.gs1_checks(barcode) 
        elif encoding == 'any':
            return True
        else:
            return False
        
    def gs1_checks(self, barcode):
        check = False     
        if '(00)' in barcode:
            sscc_code = self.get_sscc(barcode) 
            if sscc_code:        
                check = True 
        if '(01)' in barcode or '(02)' in barcode:
            product_code = self.get_product_code(barcode)
            if product_code:
                check = True 
        if '(10)' in barcode:
            serial_lot = self.get_serial_lot(barcode)
            if serial_lot:
                check = True 
        if '(37)' in barcode:
            quantity = self.get_quantity(barcode)
            if quantity:
                check = True 
        return check
    
    def get_sscc(self, barcode):
        sscc_code = False
        index_00 = barcode.find('(00)')
        sscc_code = barcode[index_00+4:]
        if '(' in sscc_code:
            index_new_bracket = sscc_code.find('(')
            sscc_code = sscc_code[:index_new_bracket]
        return sscc_code
    
    def get_product_code(self, barcode):
        product_code = False
        index_product = barcode.find('(01)')
        if index_product == -1:
            index_product = barcode.find('(02)')
        product_code = barcode[index_product+5:] #there is 0 to remove on the start of product_code
        if '(' in product_code:
            index_new_bracket = product_code.find('(')
            product_code = product_code[:index_new_bracket]
        return product_code
    
    def get_serial_lot(self, barcode):
        serial_lot = False
        index_10 = barcode.find('(10)')
        serial_lot = barcode[index_10+4:]
        if '(' in serial_lot:
            index_new_bracket = serial_lot.find('(')
            serial_lot = serial_lot[:index_new_bracket]
        return serial_lot
    
    def get_quantity(self, barcode):
        quantity = False
        index_37 = barcode.find('(37)')
        quantity = barcode[index_37+4:]
        if '(' in quantity:
            index_new_bracket = quantity.find('(')
            quantity = quantity[:index_new_bracket]
        return quantity
    