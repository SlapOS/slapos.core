from DateTime import DateTime


portal = context.getPortalObject()
portal_membership=portal.portal_membership

demo_user_functional = portal_membership.getAuthenticatedMember().getUserValue()

for support_request in portal.portal_catalog(
    portal_type="Support Request",
    simulation_state="validated",
    default_destination_decision_uid=demo_user_functional.getUid()):
  if support_request.getSimulationState() == 'validated':
    support_request.suspend()

return 'Done.'
