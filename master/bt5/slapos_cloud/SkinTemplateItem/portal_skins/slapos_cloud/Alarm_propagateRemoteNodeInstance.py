portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Compute Partition',
  free_for_request=0,
  parent_portal_type='Remote Node',
  parent__validation_state='validated',
  method_id='ComputePartition_propagateRemoteNode',
  # This alarm bruteforce checking all documents,
  # without changing them directly.
  # Increase priority to not block other activities
  method_kw={"activate_kw": {'tag': tag, 'priority': 2}},
  activate_kw={'tag': tag, 'priority': 2}
)

context.activate(after_tag=tag).getId()
