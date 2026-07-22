portal = context.getPortalObject()

# First check if project_reference is provided by the user.
member = portal.portal_membership.getAuthenticatedMember()
getGroups = getattr(member, 'getGroups', None)
if getGroups is None:
  return None

workgroup = None
user_group_list = getGroups()
workgroup_customer_on_project_user_group = "_%s_F-CUSTOMER" % context.getCodification()
for user_group in user_group_list:
  # Search for WGXXXX_PROJ-XXX_F-CUSTOMER to determinate if the user's security is
  # provided by the workgroup.
  if user_group.endswith(workgroup_customer_on_project_user_group):
    workgroup_user_id = user_group[:-len(workgroup_customer_on_project_user_group)]
    if workgroup is not None and workgroup.getUserId() != workgroup_user_id:
      raise ValueError("Duplicated found: %s, %s" % (
        workgroup_user_id, workgroup.getUserId()))

    if workgroup_user_id in user_group_list:
      workgroup = portal.portal_catalog.getResultValue(
        portal_type='Workgroup',
        user_id=workgroup_user_id)
return None
