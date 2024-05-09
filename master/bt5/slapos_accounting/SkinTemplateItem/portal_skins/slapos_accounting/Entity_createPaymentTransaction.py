from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
if not invoice_list:
  raise ValueError('You need to provide at least one Invoice transaction')

payment_tag = 'Entity_createPaymentTransaction_%s' % context.getUid()
if context.REQUEST.get(payment_tag, None) is not None:
  raise ValueError('This script was already called twice on the same transaction ')
activate_kw = {
  'tag': payment_tag
}

# Ensure all invoice use the same arrow and resource
first_invoice = invoice_list[0]
identical_dict = {
  'getSource': first_invoice.getSource(),
  'getSourceSection': first_invoice.getSourceSection(),
  'getSourcePayment': first_invoice.getSourcePayment(),
  'getDestination': first_invoice.getDestination(),
  'getDestinationSection': first_invoice.getDestinationSection(),
  'getPriceCurrency': first_invoice.getPriceCurrency(),
  'getLedger': first_invoice.getLedger(),
}

price = 0
causality_uid_list = []
# Check that all invoice matches
for invoice in invoice_list:
  for method_id, method_value in identical_dict.items():
    if getattr(invoice, method_id)() != method_value:
      raise ValueError('Invoices do not match on method: %s' % method_id)
  if invoice.total_price:
    price += invoice.total_price
    causality_uid_list.append(invoice.payment_request_uid)
  if invoice.SaleInvoiceTransaction_isLettered():
    raise ValueError('This invoice is already lettered')
  if invoice.getPortalType() != 'Sale Invoice Transaction':
    raise ValueError('Not an invoice')

if not price:
  raise ValueError('No total_price to pay')
if first_invoice.getDestinationSection() != context.getRelativeUrl():
  raise ValueError('Invoice not related to the context')

if start_date is None:
  start_date = DateTime()

if payment_mode is None:
  payment_mode = context.Base_getPaymentModeForCurrency(first_invoice.getPriceCurrencyUid())

# create the payment transaction
payment_transaction = portal.accounting_module.newContent(
  portal_type='Payment Transaction',
  created_by_builder=True,
  causality_uid_set=causality_uid_list,
  source_section=first_invoice.getSourceSection(),
  source_payment=first_invoice.getSourcePayment(),
  destination_section=first_invoice.getDestinationSection(),
  destination_section_value=context,
  start_date=start_date,
  payment_mode=payment_mode,
  #specialise
  ledger=first_invoice.getLedger(),
  resource=first_invoice.getResource(),
  destination_administration=destination_administration,
  activate_kw=activate_kw
)

getAccountForUse = context.Base_getAccountForUse

collection_account = getAccountForUse('collection')
payment_transaction.newContent(
  id='bank',
  portal_type='Accounting Transaction Line',
  source_value=collection_account,
  destination_value=collection_account,
  quantity=-price,
  activate_kw=activate_kw,
)

for index, line in enumerate(invoice_list):
  if line.total_price:
    payment_transaction.newContent(
      id="receivable%s" % index,
      title="receivable%s - %s" % (index, line.getSourceReference()),
      portal_type='Accounting Transaction Line',
      source=line.node_relative_url,
      destination_value=getAccountForUse('payable'),
      quantity=line.total_price,
      activate_kw=activate_kw,
    )

if len(payment_transaction.checkConsistency()) != 0:
  raise AssertionError(payment_transaction.checkConsistency()[0])

payment_transaction.start()

# Set a flag on the request for prevent 2 calls on the same transaction
context.REQUEST.set(payment_tag, 1)

return payment_transaction
