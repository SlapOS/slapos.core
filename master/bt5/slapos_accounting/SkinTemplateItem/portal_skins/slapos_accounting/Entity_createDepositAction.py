portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

outstanding_deposit_amount = portal.restrictedTraverse(outstanding_deposit_amount)

batch = (dialog_id is None)

# Check that the total_price matches the outstanding amount list
expected_price = context.Entity_getOutstandingDepositAmountList(
  section_uid=outstanding_deposit_amount.getSourceSectionUid(),
  resource_uid=outstanding_deposit_amount.getPriceCurrencyUid(),
  ledger_uid=outstanding_deposit_amount.getLedgerUid(),
  group_by_node=True
)[0].total_price

precision = outstanding_deposit_amount.getPriceCurrencyValue().getQuantityPrecision()
if round(total_price, precision) != round(expected_price, precision):
  if batch:
    raise ValueError('Total Amount does not match')
  return context.Base_renderForm(dialog_id, Base_translateString('Total Amount does not match'), level='error')

##################################################################
# Trigger creation of the Payment Transaction
def wrapWithShadow(entity, outstanding_amount, payment_mode):
  payment_transaction = entity.Entity_createDepositPaymentTransaction(
    outstanding_amount,
    payment_mode=payment_mode
  )
  payment_transaction.stop()
  return payment_transaction

shadow_person = portal.portal_membership.getAuthenticatedMember().getUserValue()
entity = context

payment_transaction = entity.Person_restrictMethodAsShadowUser(
  shadow_document=shadow_person,
  callable_object=wrapWithShadow,
  argument_list=[entity, context.Entity_getOutstandingDepositAmountList(
    section_uid=outstanding_deposit_amount.getSourceSectionUid(),
    resource_uid=outstanding_deposit_amount.getPriceCurrencyUid(),
    ledger_uid=outstanding_deposit_amount.getLedgerUid(),
    group_by_node=False
  ), payment_mode])

if batch:
  return payment_transaction
return payment_transaction.Base_redirect()
