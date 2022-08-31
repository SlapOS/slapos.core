portal = context.getPortalObject()

aggregate_value = portal.restrictedTraverse(aggregate)
return portal.portal_catalog.getResultValue(
  portal_type = 'Support Request',
  title = title,
  simulation_state = ["validated", "submitted", "suspended"],
  default_aggregate_uid = aggregate_value.getUid(),
)
