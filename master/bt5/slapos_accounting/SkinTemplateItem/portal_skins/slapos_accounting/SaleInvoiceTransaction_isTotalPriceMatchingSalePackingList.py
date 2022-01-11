invoice = context
if invoice.getLedger() != 'automated':
  return False

delivery_list = invoice.getCausalityValueList(portal_type='Sale Packing List')
amount = len(delivery_list)
if amount < 1:
  return False

use_list = ['use/trade/sale', 'use/trade/discount_service']
amount = sum([delivery.getTotalPrice(use=use_list) for delivery in delivery_list])

return amount == context.getTotalPrice(use=use_list)
