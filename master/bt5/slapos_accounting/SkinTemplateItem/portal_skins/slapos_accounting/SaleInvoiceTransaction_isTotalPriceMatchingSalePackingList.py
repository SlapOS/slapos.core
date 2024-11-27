invoice = context
if invoice.getLedger() != 'automated':
  return False

delivery_list = invoice.getCausalityValueList(portal_type='Sale Packing List')
amount = len(delivery_list)
if amount < 1:
  return False

use_list = ['use/trade/sale', 'use/trade/discount_service']
amount = sum([delivery.getTotalPrice(use=use_list) for delivery in delivery_list])

currency = invoice.getPriceCurrencyValue()
if currency is None:
  # completely random...
  precision = 100
else:
  precision = currency.getQuantityPrecision()
return round(amount, precision) == round(context.getTotalPrice(use=use_list), precision)
