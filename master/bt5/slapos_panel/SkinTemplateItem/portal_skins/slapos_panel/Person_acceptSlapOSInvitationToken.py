person = context
portal = context.getPortalObject()
translate = portal.Base_translateString

invitation_token = portal.invitation_token_module.restrictedTraverse(
  invitation_token
)

if (invitation_token is None) or (invitation_token.getValidationState() != 'validated'):
  return person.Base_redirect(
    'view',
    keep_items={
      'portal_status_message': translate('The invitation token can not be activated'),
      'portal_status_level': 'error'
    }
  )

assert invitation_token.getPortalType() == 'Invitation Token'
follow_up_value = invitation_token.getFollowUpValue()
category = 'destination_project'
if follow_up_value.getPortalType() == 'Workgroup':
  category = 'destination'

title = person.getTitle()
if invitation_token.getFunction() is not None:
  title = '%s: %s' % (invitation_token.getFunctionTitle(), title)

assignment_request_kw = {
  "title": title,
  "destination_decision_value" : person,
  "function" : invitation_token.getFunction(),
  category: follow_up_value.getRelativeUrl()
}

assignment_request = portal.assignment_request_module.newContent(
  portal_type='Assignment Request',
  **assignment_request_kw
)
if len(assignment_request.checkConsistency()) != 0:
  raise AssertionError(assignment_request.checkConsistency()[0])

assignment_request.submit(comment='Created Invitation Token: %s' % invitation_token.getRelativeUrl())
invitation_token.invalidate(comment='Created by Assignment Request: %s' % assignment_request.getRelativeUrl())
return person.Base_redirect(
  'view',
  keep_items={
    'portal_status_message': translate('The invitation token has been activated'),
  }
)
