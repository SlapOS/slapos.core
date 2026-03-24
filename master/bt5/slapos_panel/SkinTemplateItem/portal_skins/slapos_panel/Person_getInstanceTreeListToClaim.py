portal = context.getPortalObject()
person = context

invitation_token = portal.invitation_token_module.restrictedTraverse(
  invitation_token
)

if (invitation_token is None) or (invitation_token.getValidationState() != 'validated'):
  return []

assert invitation_token.getPortalType() == 'Invitation Token'

workgroup = invitation_token.getFollowUpValue(portal_type="Workgroup")

if workgroup is None:
  return []

assignment_request_list = portal.portal_catalog(
    portal_type='Assignment Request',
    simulation_state='validated',
    destination_decision__uid=workgroup.getUid(),
    function__uid=portal.portal_categories.function.production.customer.getUid()
  )
if len(assignment_request_list):
  project_uid_list = [
    x.getDestinationProjectUid() for x in assignment_request_list
      if x.getDestinationProject() is not None]

  if len(project_uid_list):
    return portal.portal_catalog(
      portal_type='Instance Tree',
      validation_state='validated',
      destination_section__uid=person.getUid(),
      follow_up__uid=project_uid_list
    )

return []
