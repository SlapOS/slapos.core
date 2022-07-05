from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
portal_membership=portal.portal_membership

person = portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(**kw):
  payment = portal.portal_catalog.getResultValue(
    portal_type="Payment Transaction",
    default_causality_uid=context.getUid(),
    simulation_state="stopped"
  )

  if not payment:
    return
  
  if context.getPaymentMode() == "payzen":
    return payment.PaymentTransaction_getPayzenId()
  elif context.getPaymentMode() == "wechat":
    return payment.PaymentTransaction_getWechatId()

transaction_date, transaction_id =  person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[])

if transaction_id is None:
  return

return "%s-%s" % (transaction_date.strftime("%Y%m%d"), transaction_id)
