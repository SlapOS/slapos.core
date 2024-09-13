invoice = context

if invoice.getLedger() != 'automated' and \
    not len(invoice.objectValues(portal_type="Invoice Line")):
  # Non automated invoices can be used w/o Invoice Lines for
  # the most part.
  return True

total_price = invoice.getTotalPrice()
if invoice.getTotalPrice() < 0:
  # For a negative total is from the Reversal transactions
  total_price *= -1 

accounting_price = invoice.AccountingTransaction_getTotalCredit()
precision = invoice.getPriceCurrencyValue().getQuantityPrecision()
return round(total_price, precision) == round(accounting_price, precision)
