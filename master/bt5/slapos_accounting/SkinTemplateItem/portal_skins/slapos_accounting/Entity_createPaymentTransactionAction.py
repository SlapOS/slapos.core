portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

outstanding_amount = portal.restrictedTraverse(outstanding_amount)

# Check that the total_price matches the outstanding amount list
expected_price = context.Entity_getOutstandingAmountList(
  section_uid=outstanding_amount.getSourceSectionUid(),
  resource_uid=outstanding_amount.getPriceCurrencyUid(),
  ledger_uid=outstanding_amount.getLedgerUid(),
  group_by_node=True
)[0].total_price

precision = outstanding_amount.getPriceCurrencyValue().getQuantityPrecision()
if round(total_price, precision) != round(expected_price, precision):
  return context.Base_renderForm(dialog_id, Base_translateString('Total Amount does not match'), level='error')

##################################################################
# Trigger creation of the Payment Transaction
def wrapWithShadow(entity, outstanding_amount_list, start_date, payment_mode):
  payment_transaction = entity.Entity_createPaymentTransaction(
    outstanding_amount_list,
    start_date=start_date,
    payment_mode=payment_mode
  )
  payment_transaction.stop()

  return payment_transaction

shadow_person = portal.portal_membership.getAuthenticatedMember().getUserValue()
entity = context

payment_transaction = entity.Person_restrictMethodAsShadowUser(
  shadow_document=shadow_person,
  callable_object=wrapWithShadow,
  argument_list=[entity, context.Entity_getOutstandingAmountList(
      section_uid=outstanding_amount.getSourceSectionUid(),
      resource_uid=outstanding_amount.getPriceCurrencyUid(),
      ledger_uid=outstanding_amount.getLedgerUid(),
      group_by_node=False
    ), date, payment_mode])

return payment_transaction.Base_redirect()
