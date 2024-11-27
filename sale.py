#!/usr/bin/env python
# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'
    invoice_lines = fields.Function(fields.Many2Many('account.invoice.line',
            None, None, 'Invoice Lines'), 'get_invoice_lines',
        searcher='search_invoice_lines')
    invoice_lines_ignored = fields.Many2Many(
            'sale.sale-ignored-account.invoice.line',
            'sale', 'invoice', 'Invoice Lines Ignored', readonly=True)

    def get_invoice_lines(self, name):
        return list({il.id for l in self.lines for il in l.invoice_lines})

    @classmethod
    def search_invoice_lines(cls, name, clause):
        return [('lines.invoice_lines',) + tuple(clause[1:])]

    def create_invoice(self):
        pool = Pool()
        InvoiceLine = pool.get('account.invoice.line')

        context = Transaction().context
        if (self.invoice_method == 'manual'
                and not context.get('_sale_manual_invoice', False)):
            return

        if (self.invoice_grouping_method and
                self.invoice_grouping_method == 'standalone'):
            invoice_lines = []
            for line in self.lines:
                invoice_lines.extend(line.get_invoice_line())
            if not invoice_lines:
                return

            to_save = []
            for line in invoice_lines:
                if line.type != 'line':
                    continue
                line.party = self.party
                to_save.append(line)

            if not to_save:
                return
            with Transaction().set_user(0, set_context=True):
                lines = InvoiceLine.save(to_save)
            return lines

        invoice = super().create_invoice()
        if not invoice:
            return
        for line in invoice.lines:
            line.party = invoice.party
        invoice.lines = invoice.lines
        return invoice

    def get_invoice_state(self):
        state = super().get_invoice_state()
        skips = set(x.id for x in self.invoice_lines_ignored)
        invoice_lines = [l for l in self.invoice_lines if l.id not in skips]
        if invoice_lines:
            if any(l.invoice and l.invoice.state == 'cancelled'
                    for l in invoice_lines):
                return 'exception'
            elif (state == 'paid'
                    and all(l.invoice for l in invoice_lines)
                    and all(l.invoice.state == 'paid' for l in invoice_lines)):
                return 'paid'
            elif state == 'none':
                return 'pending'
        return state

    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.setdefault('invoice_lines_ignored')
        return super().copy(sales, default=default)


class SaleIgnoredInvoiceLine(ModelSQL):
    'Sale - Ignored Invoice Line'
    __name__ = 'sale.sale-ignored-account.invoice.line'
    _table = 'sale_invoice_line_ignored_rel'
    sale = fields.Many2One('sale.sale', 'Sale',
            ondelete='CASCADE', required=True)
    invoice = fields.Many2One('account.invoice.line', 'Invoice Line',
            ondelete='RESTRICT', required=True)


class HandleInvoiceException(metaclass=PoolMeta):
    __name__ = 'sale.handle.invoice.exception'

    def transition_handle(self):
        Sale = Pool().get('sale.sale')

        state = super().transition_handle()

        sale = Sale(Transaction().context['active_id'])
        invoice_lines = []
        for invoice_line in sale.invoice_lines:
            if (invoice_line.invoice
                    and invoice_line.invoice.state == 'cancelled'):
                invoice_lines.append(invoice_line.id)
        if invoice_lines:
            Sale.write([sale], {
                    'invoice_lines_ignored': [('add', invoice_lines)],
                    })
        Sale.process([sale])
        return state
