#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import test_view, test_depends
from trytond.tests.test_tryton import doctest_setup, doctest_teardown


class SaleInvoiceLineStandaloneTestCase(unittest.TestCase):
    'Test Sale Invoice Line Standalone module'

    def setUp(self):
        trytond.tests.test_tryton.install_module(
                'sale_invoice_line_standalone')

    def test0005views(self):
        'Test views'
        test_view('sale_invoice_line_standalone')

    def test0006depends(self):
        'Test depends'
        test_depends()


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            SaleInvoiceLineStandaloneTestCase))
    suite.addTests(doctest.DocFileSuite(
            'scenario_sale_invoice_line_standalone.rst',
            setUp=doctest_setup, tearDown=doctest_teardown, encoding='UTF-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
