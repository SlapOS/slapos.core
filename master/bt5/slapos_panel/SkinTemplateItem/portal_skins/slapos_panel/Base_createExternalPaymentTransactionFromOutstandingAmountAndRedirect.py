portal = context.getPortalObject()

outstanding_amount = context
web_site = outstanding_amount.getWebSiteValue()

assert outstanding_amount.getLedgerUid() == portal.portal_categories.ledger.automated.getUid()
# assert outstanding_amount.getDestinationSectionUid() == entity.getUid()
assert web_site is not None


payment_mode = outstanding_amount.Base_getPaymentModeForCurrency(outstanding_amount.getPriceCurrencyUid())

def wrapWithShadow(outstanding_amount, payment_mode):
  portal_type = outstanding_amount.getPortalType()
  # Ensure to re-take the entity under a proper acquisition context
  # Get entity from context to preserve path
  entity = web_site.restrictedTraverse(outstanding_amount.getDestinationSection())
  method_kw = dict(
    entity_uid=entity.getUid(),
    section_uid=outstanding_amount.getSourceSectionUid(),
    resource_uid=outstanding_amount.getPriceCurrencyUid(),
    ledger_uid=outstanding_amount.getLedgerUid()
  )
  if portal_type == "Sale Invoice Transaction":
    return entity.Entity_createPaymentTransaction(
      entity.Entity_getOutstandingAmountList(
        group_by_node=False,
        **method_kw
      ),
      payment_mode=payment_mode
    )

  elif portal_type == "Subscription Request":
    # We include deposit for Subscription Requests.
    return entity.Entity_createDepositPaymentTransaction(
      entity.Entity_getOutstandingDepositAmountList(
        **method_kw),
      payment_mode=payment_mode
    )
  raise ValueError("Unsupported outstanding amount type: %s" % (portal_type))

# Ensure to re-take the entity under a proper acquisition context
# Get entity from context to preserve path
user_person = web_site.restrictedTraverse(portal.portal_membership.getAuthenticatedMember().getUserValue().getRelativeUrl())

payment_transaction = user_person.Person_restrictMethodAsShadowUser(
  shadow_document=user_person,
  callable_object=wrapWithShadow,
  argument_list=[outstanding_amount, payment_mode])

return payment_transaction.PaymentTransaction_redirectToManualPayment()
