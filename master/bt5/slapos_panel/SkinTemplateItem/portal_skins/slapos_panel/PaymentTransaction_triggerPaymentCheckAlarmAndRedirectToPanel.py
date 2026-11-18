from zExceptions import Unauthorized
portal = context.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

def wrapWithShadow(payment_transaction):
  web_site = payment_transaction.getWebSiteValue()
  assert web_site is not None

  payment_transaction.Base_reindexAndSenseAlarm([
    'slapos_payzen_update_started_payment',
    'slapos_wechat_update_started_payment',
    'slapos_cancel_sale_invoice_transaction_paied_payment_list'
  ])

  from ZTUtils import make_query
  hash_dict = {
    'page': 'slapos_master_panel_external_payment_result',
    'result': result
  }

  base = web_site.absolute_url()
  # when accessed from web_site_module/xxx_panel , absolute_url does not add the required / prefix
  if not base.endswith('/'):
    base = base + '/'

  return payment_transaction.REQUEST.RESPONSE.redirect('%s#/?%s' % (base, make_query(hash_dict)))

if person is None:
  if not portal.portal_membership.isAnonymousUser():
    return wrapWithShadow(context)
  raise Unauthorized("You must be logged in")

return person.Person_restrictMethodAsShadowUser(
  shadow_document=person,
  callable_object=wrapWithShadow,
  argument_list=[context])
