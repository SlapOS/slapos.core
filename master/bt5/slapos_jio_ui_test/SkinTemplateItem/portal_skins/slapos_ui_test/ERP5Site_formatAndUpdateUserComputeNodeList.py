from DateTime import DateTime

portal = context.getPortalObject()
portal_membership=portal.portal_membership

demo_user_functional = portal_membership.getAuthenticatedMember().getUserValue()

for compute_node in portal.portal_catalog(
    portal_type="Compute Node",
    validation_state="validated",
    default_source_administration_uid=demo_user_functional.getUid()):
  if compute_node.getValidationState() == 'validated':
    compute_node.ComputeNode_simulateSlapgridFormat()
    compute_node.activate(
      tag='ComputeNode_simulateSlapgridSoftware'
      ).ComputeNode_simulateSlapgridSoftware()
    compute_node.activate(
      after_tag='ComputeNode_simulateSlapgridSoftware'
    ).ComputeNode_simulateSlapgridInstance()

return 'Done.'
