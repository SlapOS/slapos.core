from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
if not invoice_list:
  raise ValueError('You need to provide at least one Invoice transaction')

payment_tag = 'Entity_createAccountingTransactionToConsumeDeposit_%s' % context.getUid()
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

### First, try to consume deposit amount
received_deposit_amount_list = context.Entity_getNonGroupedDepositAmountList(
  section_uid=first_invoice.getSourceSectionUid(),
  resource_uid=first_invoice.getPriceCurrencyUid(),
  ledger_uid=first_invoice.getLedgerUid(),
  group_by_node=False
)
payment_transaction = None
credit_note_transaction = None
deposit_credit_line = None

def returnOrCreatePaymentTransaction(global_payment_transaction):
  if global_payment_transaction is not None:
    return global_payment_transaction
  # create the payment transaction
  global_payment_transaction = portal.accounting_module.newContent(
    portal_type='Payment Transaction',
    title='Consume customer deposit',
    created_by_builder=True,
    causality_uid_set=causality_uid_list,
    source_section=first_invoice.getSourceSection(),
    source_payment=first_invoice.getSourcePayment(),
    destination_section=first_invoice.getDestinationSection(),
    start_date=start_date,
    payment_mode=payment_mode,
    #specialise
    ledger=first_invoice.getLedger(),
    resource=first_invoice.getResource(),
    destination_administration=destination_administration,
    activate_kw=activate_kw
  )
  return global_payment_transaction

if len(received_deposit_amount_list):

  # first, check that all deposit movement matches
  deposit_price = 0
  for deposit_amount in received_deposit_amount_list:
    for method_id, method_value in identical_dict.items():
      if getattr(deposit_amount, method_id)() != method_value:
        raise ValueError('Deposit amount do not match on method: %s' % method_id)
    if deposit_amount.total_price:
      assert deposit_amount.total_price < 0
      deposit_price -= deposit_amount.total_price
    if deposit_amount.hasGroupingReference():
      raise ValueError('This amount is already lettered')

  # if price < deposit_price:
  #   raise NotImplementedError('Can not partially consumes deposit for now...')

  getAccountForUse = context.Base_getAccountForUse
  consumed_deposit_price = 0

  # First, pay invoices if possible
  invoice_paid_line_list = []
  for index, line in enumerate(invoice_list):
    if line.total_price:
      assert 0 < line.total_price
      if (line.total_price <= deposit_price - consumed_deposit_price):
        # Deposit will fully cover this invoice
        payment_transaction = returnOrCreatePaymentTransaction(payment_transaction)
        invoice_paid_line_list.append(payment_transaction.newContent(
          id="receivable%s" % index,
          title="receivable%s - %s" % (index, line.getSourceReference()),
          portal_type='Accounting Transaction Line',
          source=line.node_relative_url,
          destination_value=getAccountForUse('payable'),
          quantity=line.total_price,
          activate_kw=activate_kw,
        ))
        consumed_deposit_price += line.total_price
        causality_uid_list.append(line.payment_request_uid)

      elif create_credit_note and (0 <= deposit_price - consumed_deposit_price):
        # Not enough deposit. Consume remaining deposit...
        payment_transaction = returnOrCreatePaymentTransaction(payment_transaction)
        not_paid_price = line.total_price - (deposit_price - consumed_deposit_price)
        invoice_paid_line_list.append(payment_transaction.newContent(
          id="partial_receivable%s" % index,
          title="partial_receivable%s - %s" % (index, line.getSourceReference()),
          portal_type='Accounting Transaction Line',
          source=line.node_relative_url,
          destination_value=getAccountForUse('payable'),
          quantity=deposit_price - consumed_deposit_price,
          activate_kw=activate_kw,
        ))

        # ...And create credit note with the remaining amount
        ratio = not_paid_price / line.total_price
        # Ensure account stays do not stay on the same debit/credit
        assert 0 < ratio
        credit_note_transaction = line.Base_createCloneDocument(batch_mode=1)
        for credit_note_line in credit_note_transaction.contentValues():
          credit_note_line.edit(quantity=-credit_note_line.getQuantity() * ratio)
        credit_note_transaction.edit(
          title='Credit note for the invoice %s' % line.getReference(),
          causality_value_list=[line, payment_transaction]
        )

        consumed_deposit_price += line.total_price
        causality_uid_list.append(line.payment_request_uid)

  # Second, consumes the deposit
  deposit_use_line_list = []
  for index, received_deposit_amount in enumerate(received_deposit_amount_list):
    assert not received_deposit_amount.hasGroupingReference()
    assert received_deposit_amount.node_relative_url == 'account_module/deposit_received'
    if received_deposit_amount.total_price:
      assert received_deposit_amount.total_price < 0
      if (-received_deposit_amount.total_price <= consumed_deposit_price):
        # Deposit can be fully consumed
        # collection_account = getAccountForUse('deposit')
        deposit_use_line_list.append(payment_transaction.newContent(
          id='use_deposit%s' % index,
          title="use_deposit%s - %s" % (index, received_deposit_amount.getSourceReference()),
          portal_type='Accounting Transaction Line',
          source='account_module/deposit_received',
          destination='account_module/deposit_paid',
          quantity=received_deposit_amount.total_price,
          activate_kw=activate_kw,
        ))
        consumed_deposit_price += received_deposit_amount.total_price
        causality_uid_list.append(received_deposit_amount.payment_request_uid)

      elif consumed_deposit_price:
        # Deposit must be partially consumed
        # Create a line to consumed it totally (to generate grouping reference)
        deposit_use_line_list.append(payment_transaction.newContent(
          id='use_deposit%s' % index,
          title="use_deposit%s - %s" % (index, received_deposit_amount.getSourceReference()),
          portal_type='Accounting Transaction Line',
          source='account_module/deposit_received',
          destination='account_module/deposit_paid',
          quantity=received_deposit_amount.total_price,
          activate_kw=activate_kw,
        ))
        # And create another line to put back some credit
        deposit_credit_line = payment_transaction.newContent(
          id='credit_partial_use_deposit%s' % index,
          title="create_partial_use_deposit%s - %s" % (index, received_deposit_amount.getSourceReference()),
          portal_type='Accounting Transaction Line',
          source='account_module/deposit_received',
          destination='account_module/deposit_paid',
          quantity=-(consumed_deposit_price + received_deposit_amount.total_price),
          activate_kw=activate_kw,
        )
        consumed_deposit_price = 0
        causality_uid_list.append(received_deposit_amount.payment_request_uid)

      else:
        # Nothing to pay anymore. Do not touch them
        continue

  if deposit_use_line_list:
    payment_transaction.edit(causality_uid_list=causality_uid_list)

    if len(payment_transaction.checkConsistency()) != 0:
      raise AssertionError(payment_transaction.checkConsistency()[0])
    payment_transaction.start()
    payment_transaction.stop()
  else:
    # No line has been created, the payment transaction must not be created
    assert payment_transaction is None

if credit_note_transaction is not None:
  if len(credit_note_transaction.checkConsistency()) != 0:
    raise AssertionError(credit_note_transaction.checkConsistency()[0])
  credit_note_transaction.start()
  credit_note_transaction.stop()
  assert credit_note_transaction.SaleInvoiceTransaction_isLettered()

if create_credit_note:
  # Create mirror transaction for invoices not handled by any deposit
  for line in invoice_list:
    if line.total_price and (not line.SaleInvoiceTransaction_isLettered()):
      # No deposit remaining. Create full invoice mirror
      line.SaleInvoiceTransaction_createReversalSaleInvoiceTransaction(batch_mode=1)
      invoice_paid_line_list.append(line)

# Assert to prevent issue. This is critical to keep them, to prevent consuming deposit twice
for line in invoice_paid_line_list + deposit_use_line_list:
  assert line.hasGroupingReference()
if deposit_credit_line:
  assert not deposit_credit_line.hasGroupingReference()

# Set a flag on the request for prevent 2 calls on the same transaction
context.REQUEST.set(payment_tag, 1)

return payment_transaction
