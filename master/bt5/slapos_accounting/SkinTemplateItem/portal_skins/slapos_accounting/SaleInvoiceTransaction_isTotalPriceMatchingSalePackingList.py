invoice = context
if invoice.getLedger() != 'automated':
  # Non automated invoices can be used
  return True

delivery_list = invoice.getCausalityValueList(portal_type='Sale Packing List')
amount = len(delivery_list)
if amount < 1:
  return False

use_list = ['use/trade/sale', 'use/trade/discount_service']
amount = sum([delivery.getTotalPrice(use=use_list) for delivery in delivery_list])

currency = invoice.getPriceCurrencyValue()
if currency is None:
  # completely random... on python3 it breaks if precision is > 27.
  precision = 25
else:
  precision = currency.getQuantityPrecision()
return round(amount, precision) == round(context.getTotalPrice(use=use_list), precision)
