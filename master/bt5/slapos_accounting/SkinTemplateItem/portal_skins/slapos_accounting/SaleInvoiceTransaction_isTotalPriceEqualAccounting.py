invoice = context

total_price = invoice.getTotalPrice()
if invoice.getTotalPrice() < 0:
  # For a negative total is from the Reversal transactions
  total_price *= -1 

accounting_price = invoice.AccountingTransaction_getTotalCredit()
precision = invoice.getPriceCurrencyValue().getQuantityPrecision()
return round(total_price, precision) == round(accounting_price, precision)
