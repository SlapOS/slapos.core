portal = context.getPortalObject()

entity = portal.portal_membership.getAuthenticatedMember().getUserValue()

outstanding_amount = context
web_site = context.getWebSiteValue()

assert web_site is not None
assert outstanding_amount.getLedgerUid() == portal.portal_categories.ledger.automated.getUid()
assert outstanding_amount.getDestinationSectionUid() == entity.getUid()

payment_mode = outstanding_amount.Base_getPaymentModeForCurrency(outstanding_amount.getPriceCurrencyUid())
assert payment_mode is not None

def wrapWithShadow(entity, outstanding_amount, payment_mode):
  return entity.Entity_createPaymentTransaction(
    entity.Entity_getOutstandingAmountList(
      section_uid=outstanding_amount.getSourceSectionUid(),
      resource_uid=outstanding_amount.getPriceCurrencyUid(),
      ledger_uid=outstanding_amount.getLedgerUid(),
      group_by_node=False
    ),
    payment_mode=payment_mode
  )

payment_transaction = entity.Person_restrictMethodAsShadowUser(
  shadow_document=entity,
  callable_object=wrapWithShadow,
  argument_list=[entity, outstanding_amount, payment_mode])

return payment_transaction.PaymentTransaction_redirectToManualPayment(web_site=web_site)
