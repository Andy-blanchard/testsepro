# -*- coding: utf-8 -*-

from odoo import http, SUPERUSER_ID
from odoo.http import request, Response

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi

import barcode
import segno

from io import BytesIO


class SVGBarcodes(http.Controller):
    @http.route(['/report/svg-barcode', '/report/svg-barcode/<type>/<path:value>'], type='http', auth="public")
    def report_barcode(self, type, value, width=0.2, height=15, dpi=300, humanreadable=0, quiet=6.5):
        """Contoller able to render barcode images thanks to python-barcode.
        Samples:
            <img t-att-src="'/report/svg-barcode/QR/%s' % o.name"/>
            <img t-att-src="'/report/svg-barcode/?type=%s&amp;value=%s&amp;width=%s&amp;height=%s' %
                ('QR', o.name, 200, 200)"/>

        :param type: Accepted types: 'EAN8', 'EAN13', 'EAN14', 'JAN', 'UPCA', 'ISBN13',
        'ISBN10', 'ISSN', 'Code39', 'PZN', 'Code128', 'ITF', 'Gs1_128', 'QR'
        :param humanreadable: Accepted values: 0 (default) or 1. 1 will insert the readable value
        at the bottom of the output image
        :param quiet: Accepted values: 0 (default) or 1. 1 will display white
        margins on left and right.
        """
        try:
            fp = BytesIO()

            if type.lower() == 'qr':
                self._report_barcode_qr(value, fp, quiet)
            else:
                self._report_barcode_standard(type, value, fp, width, height, dpi, humanreadable, quiet)

            fp.seek(0)
            return request.make_response(fp.read().decode("utf-8"), headers=[('Content-Type', 'image/svg+xml')])
        except (ValueError, AttributeError) as e:
            raise werkzeug.exceptions.HTTPException(description='Cannot convert into barcode.')

    def _report_barcode_qr(self, value, fp, quiet=1.0):
        qr = segno.make(value, error='M', boost_error=False)
        qr.save(fp,
                kind='svg',
                xmldecl=False,
                svgclass=None,
                lineclass=None,
                scale=10,
                dark='black',
                border=int(quiet) if int(quiet) > 0 else 1)

    def _report_barcode_standard(self, type, value, fp, width=0.2, height=15, dpi=300, humanreadable=0, quiet=6.5):
        if not barcode.PROVIDED_BARCODES:
            raise werkzeug.exceptions.HTTPException(description=('Barcode type %s not supported.') % (type))

        barcode_data = barcode.get_barcode_class(type)(value)
        barcode_data.write(fp, options={
            'dpi': int(dpi),
            'module_height': float(height),
            'module_width': float(width),
            'quiet_zone': float(quiet),
            'write_text': int(humanreadable) != 0
        })
