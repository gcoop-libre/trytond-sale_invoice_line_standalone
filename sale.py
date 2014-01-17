#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from sql import Table
from sql.functions import Overlay, Position

from trytond.model import ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Sale', 'SaleInvoiceLine', 'SaleIgnoredInvoiceLine',
    'HandleInvoiceException']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'
    invoice_lines = fields.Many2Many('sale.sale-account.invoice.line',
            'sale', 'line', 'Invoice Lines', readonly=True)
    invoice_lines_ignored = fields.Many2Many(
            'sale.sale-ignored-account.invoice.line',
            'sale', 'invoice', 'Invoice Lines Ignored', readonly=True)

    def create_invoice(self, invoice_type):
        pool = Pool()
        Invoice = pool.get('account.invoice')
        InvoiceLine = pool.get('account.invoice.line')

        invoice = super(Sale, self).create_invoice(invoice_type)

        if invoice:
            lines_to_delete = [l for l in invoice.lines if l.type != 'line']
            lines = [l for l in invoice.lines if l.type == 'line']
            invoice_line_ids = [l.id for l in lines]
            with Transaction().set_user(0, set_context=True):
                InvoiceLine.write(lines, {
                    'invoice': None,
                    'invoice_type': invoice.type,
                    'party': invoice.party.id,
                    'currency': invoice.currency.id,
                    'company': invoice.company.id,
                    })
                InvoiceLine.delete(lines_to_delete)
            self.write([self], {
                'invoices': [('unlink', [invoice.id])],
                'invoice_lines': [('add', invoice_line_ids)],
                })
            with Transaction().set_user(0, set_context=True):
                Invoice.cancel([invoice])
                Invoice.delete([invoice])
            return None
        return invoice

    def get_invoice_state(self):
        state = super(Sale, self).get_invoice_state()
        skips = set(x.id for x in self.invoice_lines_ignored)
        invoice_lines = [l for l in self.invoice_lines if l.id not in skips]
        if invoice_lines:
            if any(l.invoice and l.invoice.state == 'cancel'
                    for l in invoice_lines):
                return 'exception'
            elif (state == 'paid'
                    and all(l.invoice for l in invoice_lines)
                    and all(l.invoice.state == 'paid' for l in invoice_lines)):
                return 'paid'
        return state

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['invoice_lines'] = None
        default['invoice_lines_ignored'] = None
        return super(Sale, cls).copy(sales, default=default)


class SaleInvoiceLine(ModelSQL):
    'Sale - Invoice Line'
    __name__ = 'sale.sale-account.invoice.line'
    _table = 'sale_invoice_line_rel'
    sale = fields.Many2One('sale.sale', 'Sale',
            ondelete='CASCADE', select=True, required=True)
    line = fields.Many2One('account.invoice.line', 'Invoice Line',
            ondelete='RESTRICT', select=True, required=True)


class SaleIgnoredInvoiceLine(ModelSQL):
    'Sale - Ignored Invoice Line'
    __name__ = 'sale.sale-ignored-account.invoice.line'
    _table = 'sale_invoice_line_ignored_rel'
    sale = fields.Many2One('sale.sale', 'Sale',
            ondelete='CASCADE', select=True, required=True)
    invoice = fields.Many2One('account.invoice.line', 'Invoice Line',
            ondelete='RESTRICT', select=True, required=True)


class HandleInvoiceException:
    __name__ = 'sale.handle.invoice.exception'

    def transition_handle(self):
        Sale = Pool().get('sale.sale')

        state = super(HandleInvoiceException, self).transition_handle()

        sale = Sale(Transaction().context['active_id'])
        invoice_lines = []
        for invoice_line in sale.invoice_lines:
            if (invoice_line.invoice
                    and invoice_line.invoice.state == 'cancel'):
                invoice_lines.append(invoice_line.id)
        if invoice_lines:
            Sale.write([sale], {
                    'invoice_lines_ignored': [('add', invoice_lines)],
                    })
        Sale.process([sale])
        return state
