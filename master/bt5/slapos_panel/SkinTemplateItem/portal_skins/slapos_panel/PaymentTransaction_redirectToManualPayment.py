from zExceptions import Unauthorized
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(payment_transaction):
  if (payment_transaction.getPaymentMode() == "wechat"):
    return payment_transaction.PaymentTransaction_redirectToManualWechatPayment()
  elif (payment_transaction.getPaymentMode() == "payzen"):
    return payment_transaction.PaymentTransaction_redirectToManualPayzenPayment()
  else:
    return payment_transaction.PaymentTransaction_triggerPaymentCheckAlarmAndRedirectToPanel(result="contact_us")

if person is None:
  if not portal.portal_membership.isAnonymousUser():
    return wrapWithShadow(context)
  raise Unauthorized("You must be logged in")

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[context])
