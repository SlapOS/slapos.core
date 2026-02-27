person = context
portal = context.getPortalObject()
translate = portal.Base_translateString

assert person.getPortalType() == "Person"

workgroup = portal.workgroup_module.newContent(
  portal_type='Workgroup',
  title=title,
  destination_value=person
)

if len(workgroup.checkConsistency()) != 0:
  raise AssertionError(workgroup.checkConsistency()[0])

workgroup.submit(comment='Created by %s' % person.getRelativeUrl())
if batch:
  return workgroup

return workgroup.Base_redirect(
  'view',
  keep_items={
    'portal_status_message': translate('Workgroup created.'),
  }
)
