portal = context.getPortalObject()
Base_translateString = portal.Base_translateString

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

assert context.getPortalType() in ['Workgroup', 'Person']

# Search for the matching item
sql_node_list = portal.portal_catalog(
  reference=reference,
  # Project are not handled yet, as it must also move all compute node subscription at the same time
  portal_type='Remote Node',
  validation_state='validated',
  limit=2
)
if len(sql_node_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_node_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

remote_node = sql_node_list[0].getObject()

remote_node_change_request = portal.remote_node_change_request_module.newContent(
  portal_type="Remote Node Change Request",
  destination_section_value=context,
  # Repeat other values for now
  destination_project=remote_node.getDestinationProject(),
  follow_up=remote_node.getFollowUp(),
  causality_value=remote_node
)
remote_node_change_request.submit()
keep_items = {
  'portal_status_message': Base_translateString('Remote Node Change Request Created.')
}
if batch:
  return remote_node_change_request
return remote_node_change_request.Base_redirect(keep_items=keep_items)
