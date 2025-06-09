if not trade_no:
  raise ValueError("You need to provide a trade number")

portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(payment_transaction):
  payment_transaction.PaymentTransaction_updateWechatPaymentStatus()
  return payment.getSimulationState()

payment = portal.accounting_module[trade_no]

if person is None:
  if portal.portal_membership.isAnonymousUser():
    person = payment.getDestinationSectionValue()

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[payment])
