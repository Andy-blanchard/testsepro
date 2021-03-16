# -*- coding: utf-8 -*-

from odoo.tests import common

from ..common import calculate_gs1_check_digit


class TestGs1Checksum(common.TransactionCase):
    def test_gs1_checksum_1(self):
        sscc = "391200731700001604"
        gtin = "9120073170019"

        checksum = calculate_gs1_check_digit(sscc[:-1])
        self.assertEqual(checksum, int(sscc[-1]))

        checksum = calculate_gs1_check_digit(gtin[:-1])
        self.assertEqual(checksum, int(gtin[-1]))

    def test_gs1_checksum_2(self):
        sscc = "563927496312638532"
        gtin = "3245334674528"

        checksum = calculate_gs1_check_digit(sscc[:-1])
        self.assertEqual(checksum, int(sscc[-1]))

        checksum = calculate_gs1_check_digit(gtin[:-1])
        self.assertEqual(checksum, int(gtin[-1]))

    def test_gs1_checksum_3(self):
        sscc = "987654323456546359"
        gtin = "2346786423403"

        checksum = calculate_gs1_check_digit(sscc[:-1])
        self.assertEqual(checksum, int(sscc[-1]))

        checksum = calculate_gs1_check_digit(gtin[:-1])
        self.assertEqual(checksum, int(gtin[-1]))

    def test_gs1_checksum_4(self):
        sscc = "111111111111111115"
        gtin = "0000000000000"

        checksum = calculate_gs1_check_digit(sscc[:-1])
        self.assertEqual(checksum, int(sscc[-1]))

        checksum = calculate_gs1_check_digit(gtin[:-1])
        self.assertEqual(checksum, int(gtin[-1]))
