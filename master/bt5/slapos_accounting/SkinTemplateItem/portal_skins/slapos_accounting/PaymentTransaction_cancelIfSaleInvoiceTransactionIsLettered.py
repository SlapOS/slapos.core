simulation_state = context.getSimulationState()

if simulation_state != "started":
  # The payment isn't started, so ignore it
  return "Not Started"

invoice = context.getCausalityValue()
if invoice is None:
  # No invoice Related, so skip and ignore
  return

letter = invoice.SaleInvoiceTransaction_isLettered()
if letter:
  # We should ensure that the order builder won't create another document.
  context.cancel(comment="Payment is cancelled since the invoice is payed by other document,\
                          with grouping reference %s" % letter)
  return "Payment Cancelled"

return "Skipped"
