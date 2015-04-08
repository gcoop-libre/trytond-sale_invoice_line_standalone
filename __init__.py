#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from .party import *
from .sale import *
from .invoice import *


def register():
    Pool.register(
        Sale,
        SaleInvoiceLine,
        SaleIgnoredInvoiceLine,
        InvoiceLine,
        Party,
        module='sale_invoice_line_standalone', type_='model')
    Pool.register(
        HandleInvoiceException,
        ReduceLineQuantity,
        module='sale_invoice_line_standalone', type_='wizard')
