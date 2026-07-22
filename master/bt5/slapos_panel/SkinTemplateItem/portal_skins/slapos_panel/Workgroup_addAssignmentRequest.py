portal = context.getPortalObject()
Base_translateString = portal.Base_translateString
workgroup = context

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

batch = (dialog_id is None)

assert context.getPortalType() == 'Workgroup'

# Search for the matching item
sql_project_list = portal.portal_catalog(
  reference=reference,
  portal_type='Project',
  validation_state='validated',
  limit=2
)
if len(sql_project_list) != 1:
  keep_items = {
    'your_reference': reference,
    'portal_status_level': 'warning',
    'portal_status_message': Base_translateString('Unknown reference')
  }
  if batch:
    raise ValueError(keep_items['portal_status_message'] + str(len(sql_project_list)))
  return context.Base_renderForm(dialog_id, keep_items=keep_items)

project = sql_project_list[0].getObject()

# Create the assignment request
assignment_request = portal.assignment_request_module.newContent(
  portal_type='Assignment Request',
  destination_decision_value=workgroup,
  title="Client for %s: %s" % (project.getReference(), workgroup.getTitle()) ,
  destination_project_value=project,
  function='customer',
  activate_kw=activate_kw
)

assignment_request.submit()
if batch:
  return assignment_request
keep_items = {
  'portal_status_message': Base_translateString('Assignment Request created!')
}
return assignment_request.Base_redirect('view', keep_items=keep_items)
