computer = state_change['object']
portal = computer.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
computer.edit(
  allocation_scope='open/personal',
  source_administration_value=person,
)

erp5_login = computer.newContent(
  portal_type="Certificate Login",
  reference=computer.getReference()
)
erp5_login.validate()

portal.portal_workflow.doActionFor(computer, 'validate_action')
