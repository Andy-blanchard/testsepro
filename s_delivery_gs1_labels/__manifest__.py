# -*- coding: utf-8 -*-

{
    'name': 'GS1 SSCC Labels',
    'summary': 'Print GS1 SSCC labels for packages.',
    'description': """
* Generate GS1 barcodes for packaging.
* Generate GS1 barcodes for products.
* Generate GS1 SSCC numbers for packages.
* Generate valid GS1 labels for packages or pickings with packages.
* Add an alternative barcode controller which generates high resolution svg barcodes.
* Scan SSCC, Product, Lot and Quantity GS1 barcodes from Inventory and Barcode applications.

=========================================================================================


Keywords
-----------------------------------------------------------------------------------------
Packaging, Picking, GS1, SSCC, Barcodes

""",
	'author': 'Scopea',
    'contributors': ['Scopea'],
    'website': 'scopea.fr',
    'category': 'Tools',
    'version': '13.02',
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {'python': ['python-barcode', 'python-barcode[images]']},
    'depends': [
        'base',
        'stock',
        'product_expiry',
        'product', 
        'barcodes',
        'stock_barcode'
        ],
    'data': [
        'data/gs1_barcode_patterns.xml',
        'views/template.xml',
        'security/ir.model.access.csv',
        #
        'report/delivery_gs1_label_compact.xml',
        'report/delivery_gs1_report_actions.xml',
        #
        'data/delivery_gs1_sscc_sequence.xml',
        #
        'views/template.xml',
        'views/stock_quant_views.xml',        
        'views/stock_move_views.xml',
        'views/barcodes_templates.xml',
        'views/stock_barcode_templates.xml',
        
    ],
}