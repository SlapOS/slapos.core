portal = context.getPortalObject()

category_list = [portal.restrictedTraverse("portal_categories/allocation_scope/open", None)]

category_uid_list = [ i.getUid() for i in category_list if i is not None]

if category_uid_list:
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    default_allocation_scope_uid=category_uid_list,
    validation_state="validated",
    method_id='ComputeNode_checkAndUpdateCapacityScope',
    activate_kw={'tag': tag}
  )
context.activate(after_tag=tag).getId()
