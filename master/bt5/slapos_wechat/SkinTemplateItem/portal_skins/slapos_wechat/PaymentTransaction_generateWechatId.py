from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredWechatIntegrationSite())

_, transaction_id = context.PaymentTransaction_getWechatId()
if transaction_id is not None:
  # XXX raise?
  return None, None

#### Use the same ID as Payment
#### we keep the mapping just to be more like Payzen Payment
mapping_id = context.getId()

try:
  integration_site.getCategoryFromMapping(
  'Causality/%s' % context.getId().replace('-', '_'),
  create_mapping_line=True,
  create_mapping=True)
except ValueError:
  pass
integration_site.Causality[context.getId().replace('-', '_')].setDestinationReference(mapping_id)

return context.PaymentTransaction_getWechatId()
