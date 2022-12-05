from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

state = context.getSimulationState()
person = context.getSourceProjectValue(portal_type="Person")
if (state not in ('suspended', 'validated')) or \
   (person is None):
  return

outstanding_amount = person.Entity_statSlapOSOutstandingAmount()

# Amount to be ignored, as it comes from the first invoice generated
# after the subscription. We do not take it into account as no service
# was provided yet.
unpaid_invoice_amount = 0
for invoice in person.Person_getSubscriptionRequestFirstUnpaidInvoiceList():
  unpaid_invoice_amount += invoice.getTotalPrice()

# It can't be smaller, we are considernig all open invoices are from unpaid_payment_amount
if round(float(outstanding_amount), 2) == round(float(unpaid_invoice_amount), 2):
  context.invalidate(comment="Automatically disabled as balance is %s" % outstanding_amount)
  return

if (int(outstanding_amount) > 0):
  return

context.invalidate(comment="Automatically disabled as balance is %s" % outstanding_amount)
