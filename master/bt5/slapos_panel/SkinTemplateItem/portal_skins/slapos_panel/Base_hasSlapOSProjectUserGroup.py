portal = context.getPortalObject()
checked_permission = 'Access contents information'

if project_relation == 'context':
  project = context
elif project_relation == 'follow_up':
  project = context.getFollowUpValue(checked_permission=checked_permission)
elif project_relation == 'destination_project':
  project = context.getDestinationProjectValue(checked_permission=checked_permission)
elif project_relation == 'source_project':
  project = context.getSourceProjectValue(checked_permission=checked_permission)
else:
  raise ValueError('Unexpected project relation: %s' % project_relation)

if project is None or project.getPortalType() != 'Project':
  return False

project_codification = project.getCodification()

member = portal.portal_membership.getAuthenticatedMember()
getGroups = getattr(member, 'getGroups', None)
if getGroups is not None:
  user_group_list = getGroups()
  return (project.getValidationState() == 'validated') and (
    ((manager) and ('%s_F-PRODMAN' % project_codification in user_group_list)) or
    ((agent) and ('%s_F-PRODAGNT' % project_codification in user_group_list)) or
    ((customer) and ('%s_F-CUSTOMER' % project_codification in user_group_list))
  )
return False
