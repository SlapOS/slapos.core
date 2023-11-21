from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
support_request = context

causality = portal.restrictedTraverse(causality_relative_url)

customer = support_request.getDestinationDecision(portal_type='Person')
if (customer is None) and (causality.getPortalType() == 'Person'):
  customer = causality

resource = support_request.getResourceValue()

causality_portal_type = causality.getPortalType()
if causality_portal_type in ['Person', 'Sale Invoice Transaction', 'Payment Transaction']:
  project = None
elif causality_portal_type in ['Compute Node', 'Instance Tree', 'Software Installation', 'Software Instance', 'Slave Instance']:
  project = causality.getFollowUpValue()
else:
  raise NotImplementedError('No project on %s found for %s' % (causality_relative_url, support_request.getRelativeUrl()))

edit_kw = {
  'causality_value': causality,
  'resource_value': resource,
  'source_project_value': project,
  'destination_value': customer,
  'destination_decision_value': customer,
  'specialise_value': support_request.getSpecialiseValue(),
  'use_value': support_request.getUseValue(),
  'quantity_unit_value': support_request.getQuantityUnitValue(),
  'price_currency_value': support_request.getPriceCurrencyValue()
}

support_request.setCategoryList([])
support_request.edit(**edit_kw)

# Trigger migrations of related objects
portal.portal_catalog.searchAndActivate(
  method_id='Base_activateObjectMigrationToVirtualMaster',
  method_args=[support_request.getRelativeUrl()],

  portal_type=portal.getPortalEventTypeList(),
  follow_up__uid=support_request.getUid()
)
