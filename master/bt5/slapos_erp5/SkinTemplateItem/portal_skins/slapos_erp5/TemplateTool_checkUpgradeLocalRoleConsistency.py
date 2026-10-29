portal = context.getPortalObject()
result_list = []

migration_list_kw = [
  {
    'portal_type': 'Instance Tree',
    'validation_state': 'archived',
    'subscription_security_uid': '%'
  },
  {
    'portal_type': 'Project',
    'validation_state': 'invalidated',
    'project_security_uid': '%'
  },
  {
    'portal_type': 'Compute Node',
    'validation_state': 'invalidated',
    'computer_security_uid': '%'
  },
  {
    'portal_type': ['Software Instance', 'Slave Instance'],
    'specialise__validation_state': 'archived',
    'subscription_security_uid': '%'
  },
  {
    'portal_type': 'Slave Instance',
    'validation_state': 'invalidated',
    'group_security_uid': '%'
  },
  {
    'portal_type': 'Slave Instance',
    'validation_state': 'validated',
    'aggregate__uid': '%',
    'group_security_uid': None
  },
  {
    'portal_type': 'Certificate Login',
    'parent_portal_type': ['Software Instance', 'Compute Node'],
    'parent_validation_state': 'invalidated',
    'computer_security_uid': '%'
  },
]

step = 0
activate_kw = dict(priority=5, tag="%s-%s" % (script.getId(), step))
for migration_kw in migration_list_kw:
  non_migrated_instance = portal.portal_catalog(
    limit=1, **migration_kw
  )

  if (len(non_migrated_instance) == 1):
    result_list.append("all X needs updates %s" % non_migrated_instance[0].getRelativeUrl())
    if fixit:
      portal.portal_catalog.searchAndActivate(
        activate_kw=activate_kw,
        method_id='updateLocalRolesOnSecurityGroups',
        **migration_kw)
      step += 1
      activate_kw["after_tag"] = activate_kw["tag"]
      activate_kw["tag"] = "%s-%s" % (script.getId(), step)
    else:
      return result_list
return result_list
