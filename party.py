# This file is part of Tryton.  The COPYRIGHT file at the top level of this
# repository contains the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta

__metaclass__ = PoolMeta


class Party:
    __name__ = 'party.party'

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        standalone = ('standalone', 'Standalone')
        if not standalone in cls.sale_invoice_grouping_method.selection:
            cls.sale_invoice_grouping_method.selection.append(standalone)
