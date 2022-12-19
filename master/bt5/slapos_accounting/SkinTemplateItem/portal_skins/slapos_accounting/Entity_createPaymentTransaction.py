from Products.ERP5Type.Message import translateString
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
if not invoice_list:
  raise ValueError('You need to provide at least one Invoice transaction')

# For now consider a single value is passed, in future we intend to create
# a single payment per invoice.
current_invoice = invoice_list[0]
payment_tag = "sale_invoice_transaction_create_payment_%s" % current_invoice.getUid()
if context.REQUEST.get(payment_tag, None) is not None:
  raise ValueError('This script was already called twice on the same transaction ')

if current_invoice.SaleInvoiceTransaction_isLettered():
  raise ValueError('This invoice is already lettered')

context.serialize()
quantity = 0
for movement in current_invoice.searchFolder(
  portal_type='Sale Invoice Transaction Line',
  default_source_uid=[i.uid for i in context.Base_getReceivableAccountList()]):
  quantity += movement.getQuantity()

if quantity >= 0:
  raise ValueError('You cannot generate Payment Transaction for zero or negative amounts.')

current_payment = portal.accounting_module.newContent(
  portal_type="Payment Transaction",
  causality=current_invoice.getRelativeUrl(),
  source_section=current_invoice.getSourceSection(),
  destination_section=current_invoice.getDestinationSection(),
  resource=current_invoice.getResource(),
  price_currency=current_invoice.getResource(),
  specialise=current_invoice.getSpecialise(),
  payment_mode=current_invoice.getPaymentMode(),
  start_date=current_invoice.getStartDate(),
  stop_date=current_invoice.getStopDate(),
  source_payment='%s/bank_account' % current_invoice.getSourceSection(), # the other place defnied: business process
  # Workarround to not create default lines.
  created_by_builder=1
)

current_payment.newContent(
  portal_type="Accounting Transaction Line",
  quantity=-1 * quantity,
  source='account_module/receivable',
  destination='account_module/payable',
  start_date=current_invoice.getStartDate(),
  stop_date=current_invoice.getStopDate())

current_payment.newContent(
  portal_type="Accounting Transaction Line",
  quantity=1 * quantity,
  source='account_module/payment_to_encash',
  destination='account_module/payment_to_encash',
  start_date=current_invoice.getStartDate(),
  stop_date=current_invoice.getStopDate())

comment = translateString("Initialised by Entity_createPaymentTransaction.")

# Reindex with a tag to ensure that there will be no generation while the object isn't
# reindexed.
payment_tag ="sale_invoice_transaction_create_payment_%s" % current_invoice.getUid()
current_payment.activate(tag=payment_tag).immediateReindexObject()

# Call script rather them call confirm(), since it would set security and fail whenever
# start is called.
current_payment.AccountingTransaction_setReference()

comment = translateString("Initialised by Entity_createPaymentTransaction.")
current_payment.start(comment=comment)

# Set a flag on the request for prevent 2 calls on the same transaction
context.REQUEST.set(payment_tag, 1)

return current_payment
