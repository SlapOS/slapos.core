portal = context.getPortalObject()
return portal.portal_catalog(
  portal_type="Compute Node",
  validation_state="validated",
  subordination__uid=context.getUid(),
  default_strict_allocation_scope_uid="!=%s" % portal.portal_categories.allocation_scope.close.forever.getUid()
)
