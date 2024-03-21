specialise = context.getSpecialiseValue(portal_type='Sale Trade Condition')
if specialise is None or specialise.getSpecialiseValue() is None:
  # The trade model don't applies if the Trade Condition isn't attached to 
  # A business process
  return True

precision = context.getPriceCurrencyValue().getQuantityPrecision()

total_price = sum([amount.getTotalPrice() for amount in specialise.getAggregatedAmountList(context)])

invoice_tax = 0.
for line in context.getMovementList(context.getPortalInvoiceMovementTypeList()):
  if line.getUse() == 'trade/tax':
    invoice_tax += line.getTotalPrice()

return round(total_price, precision) == round(invoice_tax, precision)
