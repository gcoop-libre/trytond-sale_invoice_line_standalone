=====================================
Sale Invoice Line Standalone Scenario
=====================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import Model, Wizard
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date.today()

Install sale_invoice_line_standalone Module::

    >>> config = activate_modules('sale_invoice_line_standalone')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create sale user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> sale_user = User()
    >>> sale_user.name = 'Sale'
    >>> sale_user.login = 'sale'
    >>> sale_user.main_company = company
    >>> sale_group, = Group.find([('name', '=', 'Sales')])
    >>> sale_user.groups.append(sale_group)
    >>> sale_user.save()

Create stock user::

    >>> stock_user = User()
    >>> stock_user.name = 'Stock'
    >>> stock_user.login = 'stock'
    >>> stock_user.main_company = company
    >>> stock_group, = Group.find([('name', '=', 'Stock')])
    >>> stock_user.groups.append(stock_group)
    >>> stock_user.save()

Create an accountant user::

    >>> accountant = User()
    >>> accountant.name = 'Accountant'
    >>> accountant.login = 'accountant'
    >>> accountant.main_company = company
    >>> account_group, = Group.find([('name', '=', 'Account')])
    >>> accountant.groups.append(account_group)
    >>> accountant.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> receivable = accounts['receivable']
    >>> revenue = accounts['revenue']
    >>> expense = accounts['expense']

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.sale_invoice_grouping_method = 'standalone'
    >>> customer.save()

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])

Create category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name='Category')
    >>> account_category.accounting = True
    >>> account_category.account_expense = expense
    >>> account_category.account_revenue = revenue
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.account_category = account_category
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.purchasable = True
    >>> template.salable = True
    >>> template.list_price = Decimal('10')
    >>> template.cost_price_method = 'fixed'
    >>> product, = template.products
    >>> product.cost_price = Decimal('5')
    >>> template.save()
    >>> product, = template.products

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Sale 3 products::

    >>> config.user = sale_user.id
    >>> Sale = Model.get('sale.sale')
    >>> SaleLine = Model.get('sale.line')
    >>> sale = Sale()
    >>> sale.party = customer
    >>> sale.payment_term = payment_term
    >>> sale.invoice_method = 'order'

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 2.0

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.type = 'comment'
    >>> sale_line.description = 'Comment'

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 3.0

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.product = product
    >>> sale_line.quantity = 4.0

    >>> sale_line = SaleLine()
    >>> sale.lines.append(sale_line)
    >>> sale_line.type = 'subtotal'
    >>> sale_line.description = 'Subtotal'

    >>> sale.save()
    >>> sale.click('quote')
    >>> sale.click('confirm')
    >>> sale.state
    'processing'
    >>> sale.reload()
    >>> len(sale.moves)
    3
    >>> len(sale.shipment_returns)
    0
    >>> len(sale.invoices)
    0
    >>> len(sale.invoice_lines)
    3
    >>> len(sale.shipments)
    1

Done shipment::

    >>> config.user = stock_user.id
    >>> StockMove = Model.get('stock.move')
    >>> incoming_move = StockMove()
    >>> incoming_move.product = product
    >>> incoming_move.uom = unit
    >>> incoming_move.quantity = 10.0
    >>> incoming_move.from_location = supplier_loc
    >>> incoming_move.to_location = storage_loc
    >>> incoming_move.planned_date = today
    >>> incoming_move.effective_date = today
    >>> incoming_move.company = company
    >>> incoming_move.unit_price = Decimal('1')
    >>> incoming_move.currency = company.currency
    >>> incoming_move.click('do')
    >>> shipment = sale.shipments[0]
    >>> shipment.click('assign_try')
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')
    >>> config.user = sale_user.id
    >>> sale.reload()
    >>> sale.state
    'processing'

Create a customer invoice::

    >>> config.user = accountant.id
    >>> Invoice = Model.get('account.invoice')
    >>> invoice = Invoice()
    >>> invoice.type = 'out'
    >>> invoice.party = customer
    >>> len(invoice.lines.find())
    3
    >>> line1 = invoice.lines.find()[0]
    >>> invoice.lines.append(line1)
    >>> invoice.save()
    >>> config.user = sale.id
    >>> sale.reload()
    >>> len(sale.invoices)
    1

Create a customer invoice with an accountant::

    >>> config.user = accountant.id
    >>> invoice = Invoice()
    >>> invoice.type = 'out'
    >>> invoice.party = customer
    >>> len(invoice.lines.find())
    2
    >>> _ = [invoice.lines.append(l) for l in invoice.lines.find()]
    >>> invoice.save()

    >>> _ = invoice.lines.pop()
    >>> invoice.save()
