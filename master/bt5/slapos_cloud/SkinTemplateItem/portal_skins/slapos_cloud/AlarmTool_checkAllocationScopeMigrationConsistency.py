portal = context.getPortalObject()
result_list = []

category_path_list = ['portal_categories/allocation_scope/open/friend',
                      'portal_categories/allocation_scope/close/outdated',
                      'portal_categories/allocation_scope/close/maintenance',
                      'portal_categories/allocation_scope/close/termination',
                      'portal_categories/allocation_scope/close/forever'
                       ]

category_uid_list = []
for category_path in category_path_list:
  category = portal.restrictedTraverse(category_path, None)
  if category is None:
    continue
  
  category_uid_list.append(category.getUid())
  if category.getValidationState() != "expired":
    if fixit:
      category.expire(comment="Expired by Migration Constraint")
    else:
      result_list.append("allocation_scope/friend exists and isn't expired")

if not category_uid_list:
  # Categories were already removed so nothing to migrate
  return

migration_kw = {
  'portal_type': 'Compute Node',
  'default_allocation_scope_uid': category_uid_list
}

non_migrated_instance = portal.portal_catalog(limit=1, **migration_kw)

if len(non_migrated_instance) == 1:
  if fixit:
    portal.portal_catalog.searchAndActivate(
      activate_kw=dict(priority=5,
                       tag=script.getId(),
                       after_method_id=('immediateReindexObject',
                                        'recursiveImmediateReindexObject')),
      method_id='fixConsistency',
      **migration_kw)
  else:
    result_list.append("Compute Nodes need update %s on Allocation Scope" % non_migrated_instance[0].getRelativeUrl())

return result_list
