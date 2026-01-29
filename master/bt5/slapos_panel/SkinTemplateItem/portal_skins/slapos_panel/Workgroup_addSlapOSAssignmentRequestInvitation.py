portal = context.getPortalObject()
assert context.getPortalType() == 'Workgroup'

workgroup = context

invitation_token = portal.invitation_token_module.newContent(
  portal_type="Invitation Token",
  # This is probably a limitation of the design which will
  # lead to an if later on, but for simplicity keep this.
  follow_up_value=workgroup
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
