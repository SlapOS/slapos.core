specialise = context.getSpecialiseValue(portal_type='Sale Trade Condition')
if specialise is None or specialise.getSpecialiseValue() is None:
  # The trade model don't applies if the Trade Condition isn't attached to 
  # A business process
  return True

amount_list = specialise.getAggregatedAmountList(context)

precision = context.getPriceCurrencyValue().getQuantityPrecision()

if len(amount_list) == 1:
  # XXX why only one amount is expected?
  amount = amount_list[0]
  total_price = amount.getTotalPrice()
elif len(amount_list) == 0:
  # Not all service will generate tax (deposit)
  total_price = 0
else:
  return False

invoice_tax = 0.
for line in context.getMovementList(context.getPortalInvoiceMovementTypeList()):
  if line.getUse() == 'trade/tax':
    invoice_tax += line.getTotalPrice()

return round(total_price, precision) == round(invoice_tax, precision)
