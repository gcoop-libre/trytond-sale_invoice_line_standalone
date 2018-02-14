#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import party
from . import sale
from . import invoice


def register():
    Pool.register(
        sale.Sale,
        sale.SaleLine,
        sale.SaleIgnoredInvoiceLine,
        invoice.InvoiceLine,
        party.Party,
        module='sale_invoice_line_standalone', type_='model')
    Pool.register(
        sale.HandleInvoiceException,
        module='sale_invoice_line_standalone', type_='wizard')
