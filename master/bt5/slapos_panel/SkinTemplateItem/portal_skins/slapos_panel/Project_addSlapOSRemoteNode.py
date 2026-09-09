from Products.ERP5Type.Message import translateString

portal = context.getPortalObject()
project = context
person = portal.portal_membership.getAuthenticatedMember().getUserValue()
project_value = portal.restrictedTraverse(destination_project)

remote_node = portal.compute_node_module.newContent(
  portal_type='Remote Node',
  title=title,
  # directly set the workgroup, to reduce number of migrations
  # if user leaves the project
  destination_section_value=person.getTypeBasedMethod('getSlaposActorRequester')(project_value),
  destination_project_value=project_value,
  follow_up_value=project,
  allocation_scope='open'
)
for i in range(partition_amount):
  computer_partition = remote_node.newContent(
    portal_type="Compute Partition",
    reference="slapremote%i" % i
  )
  computer_partition.markFree()
  computer_partition.validate()
remote_node.validate()

return remote_node.Base_redirect(
  keep_items={
    'portal_status_message': translateString('New Remote Node created.')
  }
)
