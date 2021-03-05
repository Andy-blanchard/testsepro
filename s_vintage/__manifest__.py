# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP - Vintage',
	'author': "II-Lifting/Scopea",
    'website': "http://www.scopea.fr",
	'version': '13.0.001',
    'description': """Manage mrp with vintage.""",
    'depends': ['stock', 'mrp', 'product', 'mrp_workorder'],
	
    'data': [
        'views/mrp_workorder_views.xml',
        'views/mrp_product_produce.xml',
    ],
	
    'installable': True,
    'application': False,

}