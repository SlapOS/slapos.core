node = state_change['object']

uid_list = [child.getUid() for child in node.contentValues(
  portal_types="Compute Partition")]

uid_list.append(node.getUid())

node.getPortalObject().portal_catalog.searchAndActivate(
  portal_type=["Software Instance", "Slave Instance", "Software Installation"],
  aggregate__uid=uid_list,
  method_id='updateLocalRolesOnSecurityGroups'
)
