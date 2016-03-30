#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Sale', 'SaleInvoiceLine', 'SaleIgnoredInvoiceLine',
    'HandleInvoiceException']


class Sale:
    __metaclass__ = PoolMeta
    __name__ = 'sale.sale'
    invoice_lines = fields.Many2Many('sale.sale-account.invoice.line',
            'sale', 'line', 'Invoice Lines', readonly=True)
    invoice_lines_ignored = fields.Many2Many(
            'sale.sale-ignored-account.invoice.line',
            'sale', 'invoice', 'Invoice Lines Ignored', readonly=True)

    def create_invoice(self):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        if (self.invoice_grouping_method and
                self.invoice_grouping_method == 'standalone'):
            invoice_lines = self._get_invoice_line_sale_line()
            if not invoice_lines:
                return

            to_create = []
            for lines in invoice_lines.values():
                for line in lines:
                    if line.type != 'line':
                        continue
                    to_create.append(line._save_values)

            if not to_create:
                return
            with Transaction().set_user(0, set_context=True):
                lines = InvoiceLine.create(to_create)
            self.write([self], {
                'invoice_lines': [('add', lines)],
                })
            return lines
        return super(Sale, self).create_invoice()

    def _get_invoice_line_sale_line(self):
        invoice_lines = super(Sale, self)._get_invoice_line_sale_line()
        invoice = self._get_invoice_sale()
        for lines in invoice_lines.values():
            for line in lines:
                line.invoice_type = invoice.type
                line.party = invoice.party
                line.currency = invoice.currency
                line.company = invoice.company
                line.invoice = None
        return invoice_lines

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
    __metaclass__ = PoolMeta
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
