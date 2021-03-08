# -*- coding: utf-8 -*-

GLN_LENGTH = 9
GTIN_LENGTH = 13
GTIN_14_LENGTH = 14
SSCC_LENGTH = 18
SSCC_EXTENSION_DIGIT = 3


def calculate_gs1_check_digit(barcode_number_without_checkdigit):
    check_sum = 0
    for i, char in enumerate(reversed(barcode_number_without_checkdigit)):
        if i % 2 == 0:
            check_sum += int(char) * 3
        else:
            check_sum += int(char)

    mod = check_sum % 10
    check_digit = 10 - mod
    if check_digit == 10:
        check_digit = 0

    return check_digit


def check_if_product_barcode_is_assigned(env, barcode):
    if not env:
        return True

    products = env['product.product'].search([
        ('barcode', '=', barcode)
    ])

    if len(products) > 0:
        return True
    else:
        return False


def generate_barcode(env):
    if not env:
        return False

    barcode = env['ir.sequence'].next_by_code('s.gs1.product.barcode')
    return barcode + str(calculate_gs1_check_digit(barcode))


def get_gs1_barcode(env):
    if not env:
        return False

    barcode = generate_barcode(env)
    while check_if_product_barcode_is_assigned(env, barcode) is True:
        barcode = generate_barcode(env)

    return barcode
