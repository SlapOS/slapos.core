portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
  portal_type='Compute Partition',
  free_for_request=0,
  parent_portal_type='Remote Node',
  parent__validation_state='validated',
  method_id='ComputePartition_propagateRemoteNode',
  method_kw={"activate_kw": {'tag': tag}},
  activate_kw={'tag': tag}
)

context.activate(after_tag=tag).getId()
