#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.sale_invoice_line_standalone.tests.test_sale_invoice_line_standalone import suite
except ImportError:
    from .test_sale_invoice_line_standalone import suite

__all__ = ['suite']
