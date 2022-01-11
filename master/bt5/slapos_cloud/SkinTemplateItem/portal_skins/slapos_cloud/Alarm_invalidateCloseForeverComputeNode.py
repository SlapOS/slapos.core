""" Clean up, and invalidate all close forever compute node that 
  have no instances allocated on it.
"""
portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Compute Node',
  validation_state='validated',
  allocation_scope__uid=[
    portal.portal_categories.allocation_scope.close.forever.getUid()
  ],
  method_id="ComputeNode_invalidateIfEmpty",
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
