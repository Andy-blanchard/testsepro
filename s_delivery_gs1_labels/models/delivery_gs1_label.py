# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging
from ..common import GTIN_LENGTH, SSCC_LENGTH

_logger = logging.getLogger(__name__)


class GS1AbstractLabelPackageReport(models.AbstractModel):
    _name = 'base.report.s_delivery_gs1_labels'
    _description = 'Base report model for GS1 specification validation.'

    @api.model
    def _get_report_name_for_model(self):
        raise NotImplementedError('Method _get_report_name() undefined on %s' % self)

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name(
            self._get_report_name_for_model()
        )

        docs = self.env[report.model].browse(docids)
        base_error_msg = _('Can not print SSCC shipping label(s), one or more errors found:')
        report_data = docs
        if (report.model == 'stock.picking'):
            report_data = self._check_if_packages_available(base_error_msg, report_data)

        self._check_if_ids_available(base_error_msg, report_data)
        self._check_if_products_assigned(base_error_msg, report_data)
        self._check_invalid_gs1_numbers(base_error_msg, report_data)

        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }

    def _check_if_packages_available(self, error_msg, docs):
        report_data = docs.mapped('move_line_ids') \
            .filtered(lambda ml: ml.result_package_id) \
            .mapped('result_package_id')

        if not report_data or len(report_data) <= 0:
            error_msg += _('\n\n - No packages found in selected picking(s) (%s)') % (', '.join(docs.mapped('name')))
            raise ValidationError(error_msg)

        return report_data

    def _check_invalid_gs1_numbers(self, error_msg, docs):
        show_error = False

        invalid_ssccs = docs.filtered(lambda x: not x.sscc_number or len(x.sscc_number) != SSCC_LENGTH).mapped(
            'display_name')
        if invalid_ssccs and len(invalid_ssccs) > 0:
            show_error = True
            error_msg += _('\n\n - Following packages have no valid SSCC number with 18 characters: \n') + \
                         ', '.join(invalid_ssccs)

        if any(any(any(not z.barcode or len(z.barcode) != GTIN_LENGTH for z in y.product_id) for y in x.quant_ids) for x
               in docs):
            show_error = True
            error_msg += _('\n\n - Following products do not have a valid barcode with 13 characters: \n')
            invalid_products = []
            for quant in docs:
                for quant_id in quant.quant_ids:
                    invalid_products.extend(
                        quant_id.product_id.filtered(lambda x: not x.barcode or len(x.barcode) != GTIN_LENGTH).mapped(
                            'display_name'))

            error_msg += ', '.join(invalid_products)

        if show_error:
            raise ValidationError(error_msg)

    def _check_if_ids_available(self, error_msg, docs):
        if not docs or len(docs) <= 0:
            error_msg += _('\n\n No valid packages to print available.')

            raise ValidationError(error_msg)

    def _check_if_products_assigned(self, error_msg, docs):
        invalid_packages = docs.filtered(lambda x: not x.quant_ids or len(x.quant_ids) <= 0) \
            .mapped('display_name')
        if invalid_packages and len(invalid_packages) > 0:
            error_msg += _('\n\n - Following packages have no products assigned. Maybe you have not assigned any quantities and validated your related pickings: \n') + \
                         ', '.join(invalid_packages)
            raise ValidationError(error_msg)


class GS1LabelPackageReport(models.AbstractModel):
    _name = 'report.s_delivery_gs1_labels.gs1_label_package'
    _inherit = "base.report.s_delivery_gs1_labels"
    _description = 'Report model for GS1 labels with GS1 specification validation.'

    def _get_report_name_for_model(self):
        return 's_delivery_gs1_labels.gs1_label_package'


class GS1LabelPickingReport(models.AbstractModel):
    _name = 'report.s_delivery_gs1_labels.gs1_label_picking'
    _inherit = "base.report.s_delivery_gs1_labels"
    _description = 'Report model for GS1 labels with GS1 specification validation.'

    def _get_report_name_for_model(self):
        return 's_delivery_gs1_labels.gs1_label_picking'
