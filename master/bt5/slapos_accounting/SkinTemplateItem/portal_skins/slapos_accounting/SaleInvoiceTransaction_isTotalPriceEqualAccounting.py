invoice = context

specialise = context.getSpecialiseValue(portal_type='Sale Trade Condition')
if specialise.getSpecialiseValue() is None:
  if not len(invoice.objectValues(portal_type="Invoice Line")):
    # The trade model don't applies if the Trade Condition isn't attached to
    # A business process
    return True

total_price = invoice.getTotalPrice()
if invoice.getTotalPrice() < 0:
  # For a negative total is from the Reversal transactions
  total_price *= -1 

accounting_price = invoice.AccountingTransaction_getTotalCredit()
precision = invoice.getPriceCurrencyValue().getQuantityPrecision()
return round(total_price, precision) == round(accounting_price, precision)
