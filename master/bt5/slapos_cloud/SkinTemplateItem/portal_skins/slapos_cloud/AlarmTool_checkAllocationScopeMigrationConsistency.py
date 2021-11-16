portal = context.getPortalObject()
result_list = []

category = portal.restrictedTraverse("portal_categories/allocation_scope/open/friend", None)
if category is None:
  # Category already migrated nothing to do
  return []

if category.getValidationState() != "expired":
  if fixit:
    category.expire(comment="Expired by Migration Constraint")
  else:
    result_list.append("allocation_scope/friend exists and isn't expired")

migration_kw = {
  'portal_type': 'Compute Node',
  'default_allocation_scope_uid': category.getUid()
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
