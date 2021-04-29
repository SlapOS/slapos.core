simulation_state = context.getSimulationState()

if simulation_state != "started":
  # The payment isn't started, so ignore it
  return "Not Started"

portal = context.getPortalObject()

paid = False

def isNodeFromLineReceivable(line):
  node_value = line.getSourceValue(portal_type='Account')
  return node_value.getAccountType() == 'asset/receivable'

invoice = context.getCausalityValue()

if invoice is None:
  # No invoice Related, so skip and ignore
  return

line_found = False
line_list = invoice.getMovementList(portal.getPortalAccountingMovementTypeList())
if not len(line_list):
  # Ignore since lines to group don't exist yet
  return

for line in line_list:
  if isNodeFromLineReceivable(line):
    line_found = True
    if line.hasGroupingReference():
      paid = True
      letter = line.getGroupingReference()
      break

if line_found and paid:
  # We should ensure that the order builder won't create another document.
  context.edit(payment_mode=None)
  context.cancel(comment="Payment is cancelled since the invoice is payed by other document,\
                          with grouping reference %s" % letter)
  
  # Should be safe now to fix everything XXXXXXX
  invoice.SaleInvoiceTransaction_resetPaymentMode()

  return "Payment Cancelled"

return "Skipped"
