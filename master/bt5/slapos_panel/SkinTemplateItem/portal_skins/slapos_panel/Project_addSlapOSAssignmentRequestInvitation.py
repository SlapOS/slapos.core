assert function in ['production/manager', 'customer']

portal = context.getPortalObject()
project = context

invitation_token = portal.invitation_token_module.newContent(
  portal_type="Invitation Token",
  follow_up_value=project,
  function_value=portal.portal_categories.function.restrictedTraverse(function)
)
invitation_token.validate()
# Access the token after it has been validated, to ensure
# current user has permission to see it
# (user must be project manager)
invitation_token_reference = invitation_token.getId()

return context.Base_renderForm(
  'Project_viewSlapOSAssignmentRequestInvitationDialog',
  message=portal.Base_translateString('New Invitation Token created.'),
  keep_items={
    'your_invitation_token': invitation_token_reference
  }
)
