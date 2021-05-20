invoice = context
specialise = context.getPortalObject().portal_preferences.getPreferredAggregatedSaleTradeCondition()
if invoice.getSpecialise() != specialise:
  return False

if len(invoice.getCausalityRelatedList(portal_type=['Cloud Contract', 'Subscription Request'])) > 0:
  # Nothing to compare
  return True

delivery_list = invoice.getCausalityValueList(portal_type='Sale Packing List')
amount = len(delivery_list)
if amount < 1:
  return False

amount = sum([delivery.getTotalPrice(use='use/trade/sale') for delivery in delivery_list])

return amount == context.getTotalPrice(use='use/trade/sale')
