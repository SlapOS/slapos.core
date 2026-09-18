portal = context.getPortalObject()
workgroup = context
Base_translateString = portal.Base_translateString

if (not listbox_uid) and (not project_uid) and (not customer_uid):
  return context.Base_renderForm('Workgroup_viewClaimSlaposMemberInstanceDialog', message=Base_translateString('No Instance Tree selected'), level='error')

instance_tree_list = portal.portal_catalog(
  uid=listbox_uid,
  follow_up__uid=project_uid,
  destination_section__uid=customer_uid
)

if (len(instance_tree_list) == 0) or (len(instance_tree_list) != len(listbox_uid)):
  return context.Base_renderForm('Workgroup_viewClaimSlaposMemberInstanceDialog', message=Base_translateString('Please reconfirm the Instance Tree list'), level='error')

for instance_tree in instance_tree_list:
  workgroup.Actor_claimSlaposItemSubscription(instance_tree.getReference(), None)
return context.Base_redirect(keep_items={'portal_status_message': Base_translateString('Instance Trees claimed.')})
