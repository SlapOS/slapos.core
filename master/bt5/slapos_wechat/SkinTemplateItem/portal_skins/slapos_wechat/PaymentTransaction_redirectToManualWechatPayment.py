from zExceptions import Unauthorized
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(payment_transaction, web_site, person_relative_url):

  vads_url_dict = payment_transaction.PaymentTransaction_getVADSUrlDict()

  _ , transaction_id = payment_transaction.PaymentTransaction_getWechatId()
  vads_url_already_registered = vads_url_dict.pop('vads_url_already_registered')
  if transaction_id is not None:
    return context.REQUEST.RESPONSE.redirect(vads_url_already_registered)

  system_event = payment_transaction.PaymentTransaction_createWechatEvent(
    title='User navigation script for %s' % payment_transaction.getTitle(),
    destination_section=person_relative_url,
  )
  if web_site:
    context.REQUEST.set('base_url', '%s/wechat_payment' % web_site.absolute_url())
  system_event.generateManualPaymentPage()

  return system_event.contentValues(
    portal_type="Wechat Event Message")[0].getTextContent()

if person is None:
  if not portal.portal_membership.isAnonymousUser():
    return wrapWithShadow(context, web_site, context.getDestinationSection())
  raise Unauthorized("You must be logged in")

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[context, web_site, person.getRelativeUrl()])
