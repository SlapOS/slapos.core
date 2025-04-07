from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
accounting_transaction_line = context
payment_transaction = accounting_transaction_line.getParentValue()
title = "mirror %s for customer" % payment_transaction.getTitle()
account = portal.Base_getAccountForUse('asset_receivable_subscriber')

assert payment_transaction.getPortalType() == 'Payment Transaction'
assert accounting_transaction_line.getSource(portal_type='Account') == account.getRelativeUrl()
assert not accounting_transaction_line.getDestination(portal_type='Account')
assert payment_transaction.getLedger() == 'automated'
assert payment_transaction.getSimulationState() in ['stopped', 'delivered']

if accounting_transaction_line.getGroupingReference(None) is not None:
  # line is already grouped
  return

# Create mirroring payment transaction
# required to have grouping reference with the invoice
customer_payment_transaction = portal.accounting_module.newContent(
  title=title,
  portal_type=payment_transaction.getPortalType(),
  start_date=payment_transaction.getStartDate(),
  stop_date=payment_transaction.getStopDate(),
  specialise_value=payment_transaction.getSpecialiseValue(),
  destination=payment_transaction.getSource(),
  destination_section=payment_transaction.getSourceSection(),
  destination_decision=payment_transaction.getSourceDecision(),
  destination_project=payment_transaction.getSourceProject(),
  source=payment_transaction.getDestination(),
  source_section=payment_transaction.getDestinationSection(),
  source_decision=payment_transaction.getDestinationDecision(),
  source_project=payment_transaction.getDestinationProject(),
  payment_mode=payment_transaction.getPaymentMode(),
  ledger=payment_transaction.getLedger(),
  resource=payment_transaction.getResource(),
  # Attach the payment transaction to trigger the automatic grouping
  causality_value=payment_transaction,
  created_by_builder=1, # XXX this prevent init script from creating lines.
  activate_kw=activate_kw
)

getAccountForUse = context.Base_getAccountForUse

# receivable
customer_payment_transaction.newContent(
  id='payable',
  portal_type='Accounting Transaction Line',
  quantity=payment_transaction.PaymentTransaction_getTotalPayablePrice(),
  source_value=getAccountForUse('payable'),
  activate_kw=activate_kw
)

# bank
customer_payment_transaction.newContent(
  id='bank',
  portal_type='Accounting Transaction Line',
  quantity=-payment_transaction.PaymentTransaction_getTotalPayablePrice(),
  # XXX XXX use another account?
  source_value='account_module/payment_to_encash',
  activate_kw=activate_kw
)

if len(customer_payment_transaction.checkConsistency()) != 0:
  raise AssertionError(customer_payment_transaction.checkConsistency()[0])

customer_payment_transaction.start(comment=translateString("Payment Transaction stopped."))
customer_payment_transaction.stop(comment=translateString("Payment Transaction stopped."))

payment_transaction.reindexObject(activate_kw=activate_kw)
customer_payment_transaction.reindexObject(activate_kw=activate_kw)

if accounting_transaction_line.getGroupingReference(None) is None:
  # This check is required to prevent getting an infinite loop
  # in the alarm which create infinite number of payment transaction
  raise ValueError('%s should have been grouped' % accounting_transaction_line.getRelativeUrl())
