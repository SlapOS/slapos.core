project = state_change['object']
portal = project.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type=[
    'Compute Node', 'Remote Node', 'Instance Node', 'Compute Model', 'Compute Network',
  ],
  follow_up__uid=project.getUid(),
  method_id='updateLocalRolesOnSecurityGroups'
)
