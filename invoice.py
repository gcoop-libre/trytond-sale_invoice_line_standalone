# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['InvoiceLine']


class InvoiceLine(metaclass=PoolMeta):
    __name__ = 'account.invoice.line'

    @classmethod
    def __setup__(cls):
        super(InvoiceLine, cls).__setup__()
        cls._error_messages.update({
                'delete_sale_invoice_line': ('You can not delete '
                    'invoice lines that comes from a sale.'),
                })

    @classmethod
    def delete(cls, lines):
        SaleLine = Pool().get('sale.line')
        if (not Transaction().context.get('allow_remove_sale_invoice_lines')
                and any(l for l in lines
                    if isinstance(l.origin, SaleLine) and l.type == 'line')):
            cls.raise_user_error('delete_sale_invoice_line')
        super(InvoiceLine, cls).delete(lines)
