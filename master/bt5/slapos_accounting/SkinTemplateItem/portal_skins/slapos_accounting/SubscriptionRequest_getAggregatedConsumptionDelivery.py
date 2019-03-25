integration_site = context.getPortalObject().restrictedTraverse(
    'portal_integrations/slapos_aggregated_consumption_delivery_integration_site')

subscription_id = context.getId().replace('-', '_')
try:
  mapping = integration_site.getCategoryFromMapping('Causality/%s' % subscription_id, create_mapping_line=True, create_mapping=True)
except ValueError:
  return None
return context.restrictedTraverse(mapping)
