portal = context.getPortalObject()
person = context

assignment_list = portal.portal_catalog(
  portal_type='Assignment',
  parent_uid=person.getUid(),
  validation_state='open',
  destination__portal_type='Workgroup'
)

# Return the list of Workgroup Uids
return [assignment.getDestinationUid() for assignment in assignment_list]
