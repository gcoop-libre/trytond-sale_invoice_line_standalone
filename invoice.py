# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['InvoiceLine']
__metaclass__ = PoolMeta


class InvoiceLine:
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        cls._error_messages.update({
                'delete_sale_invoice_line': ('You can not delete '
                    'invoice lines that comes from a sale.'),
                })

    @classmethod
    def write(cls, *args):
        Sale = Pool().get('sale.sale')
        actions = iter(args)
        for lines, values in zip(actions, actions):
            if 'invoice' in values:
                with Transaction().set_user(0, set_context=True):
                    sales = Sale.search([
                            ('invoice_lines', 'in', [l.id for l in lines]),
                            ])
                    if values['invoice']:
                        Sale.write(sales, {
                            'invoices': [('add', [values['invoice']])],
                            })
                    else:
                        for sale in sales:
                            invoice_ids = list(set([x.invoice.id for x
                                        in sale.invoice_lines
                                        if x.invoice and x.id in lines])
                                - set([x.invoice.id for x
                                        in sale.invoice_lines
                                        if x.invoice and x.id not in lines]))
                            Sale.write([sale], {
                                'invoices': [('unlink', invoice_ids)],
                                })

        return super(InvoiceLine, cls).write(*args)

    @classmethod
    def delete(cls, lines):
        SaleLine = Pool().get('sale.line')
        if (not Transaction().context.get('allow_remove_sale_invoice_lines')
                and any(l for l in lines
                    if isinstance(l.origin, SaleLine) and l.type == 'line')):
            cls.raise_user_error('delete_sale_invoice_line')
        super(InvoiceLine, cls).delete(lines)
