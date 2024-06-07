instance_tree = state_change['object']
portal = instance_tree.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type=['Software Instance', 'Slave Instance'],
  specialise__uid=instance_tree.getUid(),
  method_id='updateLocalRolesOnSecurityGroups'
)
