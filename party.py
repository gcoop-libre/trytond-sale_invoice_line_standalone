# This file is part of the sale_invoice_line_standalone module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta

__all__ = ['Party']


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        standalone = ('standalone', 'Standalone')
        if standalone not in cls.sale_invoice_grouping_method.selection:
            cls.sale_invoice_grouping_method.selection.append(standalone)
