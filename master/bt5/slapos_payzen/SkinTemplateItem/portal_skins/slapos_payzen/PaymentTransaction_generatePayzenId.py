from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

_, transaction_id = context.PaymentTransaction_getPayzenId()
if transaction_id is not None:
  # XXX raise?
  return None, None

now = DateTime().toZone('UTC')
today = now.asdatetime().strftime('%Y%m%d')

preferred_integration_site = portal.portal_preferences.getPreferredPayzenIntegrationSite()
integration_site = portal.restrictedTraverse(preferred_integration_site)

if integration_site is None or not preferred_integration_site:
  raise ValueError("Integration Site not found or not configured: %s" %
    preferred_integration_site)

transaction_id = str(portal.portal_ids.generateNewId(
  id_group='%s_%s' % (integration_site.getRelativeUrl(), today),
  id_generator='uid')).zfill(6)


try:
  # Init for use later.
  integration_site.getCategoryFromMapping(
    'Causality/%s' % context.getId().replace('-', '_'),
    create_mapping_line=True,
    create_mapping=True)
except ValueError:
  pass

mapping_id = '%s_%s' % (today, transaction_id)
integration_site.Causality[context.getId().replace('-', '_')].setDestinationReference(mapping_id)

return context.PaymentTransaction_getPayzenId()
