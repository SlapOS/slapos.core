from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

item = context
portal = context.getPortalObject()

if item.getValidationState() in ['invalidated', 'archived']:
  return 'todestroy'

# If no open order, subscription must be approved
open_sale_order_movement_list = portal.portal_catalog(
  portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
  aggregate__uid=item.getUid(),
  validation_state='validated',
  limit=1
)

if len(open_sale_order_movement_list) == 0:
  return "not_subscribed"

# Check if there are some ongoing Regularisation Request
# if so, return to_pay
entity_uid = None
item_portal_type = item.getPortalType()
if item_portal_type == 'Instance Tree':
  entity_uid = item.getDestinationSectionUid()
elif item_portal_type == 'Project':
  entity_uid = item.getDestinationUid()
elif item_portal_type == 'Compute Node':
  project = item.getFollowUpValue()
  if project is not None:
    entity_uid = project.getDestinationUid()
else:
  raise NotImplementedError('Unsupported item %s' % item.getRelativeUrl())

regularisation_request_list = portal.portal_catalog(
  portal_type='Regularisation Request',
  destination__uid=entity_uid or -1,
  simulation_state='suspended',
  resource__uid=[
    portal.service_module.slapos_crm_stop_acknowledgement.getUid(),
    portal.service_module.slapos_crm_delete_reminder.getUid(),
    portal.service_module.slapos_crm_delete_acknowledgement.getUid(),
  ],
  limit=1
)
if len(regularisation_request_list) == 1:
  return "nopaid"

return "subscribed"
