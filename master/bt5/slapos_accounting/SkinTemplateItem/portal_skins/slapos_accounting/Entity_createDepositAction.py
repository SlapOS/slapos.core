portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

outstanding_deposit_amount = portal.restrictedTraverse(outstanding_deposit_amount)

# Check that the total_price matches the outstanding amount list
expected_price = context.Entity_getOutstandingDepositAmountList(
  section_uid=outstanding_deposit_amount.getSourceSectionUid(),
  resource_uid=outstanding_deposit_amount.getPriceCurrencyUid(),
  ledger_uid=outstanding_deposit_amount.getLedgerUid(),
  group_by_node=True
)[0].total_price

precision = outstanding_deposit_amount.getPriceCurrencyValue().getQuantityPrecision()
if round(total_price, precision) != round(expected_price, precision):
  return context.Base_renderForm(dialog_id, Base_translateString('Total Amount does not match'), level='error')


payment_transaction = context.Entity_createDepositPaymentTransaction(
  context.Entity_getOutstandingDepositAmountList(
    section_uid=outstanding_deposit_amount.getSourceSectionUid(),
    resource_uid=outstanding_deposit_amount.getPriceCurrencyUid(),
    ledger_uid=outstanding_deposit_amount.getLedgerUid(),
    group_by_node=False
  ),
  # start_date=date,
  payment_mode=payment_mode
)
payment_transaction.stop()

return payment_transaction.Base_redirect()
