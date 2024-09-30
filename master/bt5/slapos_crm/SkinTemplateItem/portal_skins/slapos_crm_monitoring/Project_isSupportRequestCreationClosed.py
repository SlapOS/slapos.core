portal = context.getPortalObject()

assert context.getPortalType() == 'Project', "context is not a project"
limit = int(portal.portal_preferences.getPreferredSupportRequestCreationLimit(5))

kw = {
  'limit': limit,
  'portal_type': 'Support Request',
  'simulation_state': ["validated", "submitted", "suspended"],
  'source_project__uid': context.getUid(),
  'resource__uid': portal.service_module.slapos_crm_monitoring.getUid()
}

return limit <= int(portal.portal_catalog.countResults(**kw)[0][0])
