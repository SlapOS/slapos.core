from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
remote_node_change_request = context
assert remote_node_change_request.getPortalType() == 'Remote Node Change Request'
assert remote_node_change_request.getSimulationState() == 'submitted'
remote_node_change_request.reindexObject(activate_kw=activate_kw)

remote_node = remote_node_change_request.getCausalityValue(portal_type='Remote Node')
remote_project = remote_node.getDestinationProjectValue(portal_type='Project')
remote_user = remote_node_change_request.getDestinationSectionValue()

# XXX Ensure that user is customer on destination project, else no claim should be done.
remote_entity = remote_node.getDestinationSectionValue(portal_type=['Person', 'Workgroup'])

search_kw = dict(
  portal_type=['Slave Instance', 'Software Instance'],
  aggregate__uid=[p.uid for p in remote_node.contentValues(portal_type='Compute Partition')],
  validation_state='validated'
)

for local_instance in portal.portal_catalog(**search_kw):
  remote_instance_tree_list = portal.portal_catalog(
    portal_type='Instance Tree',
    validation_state='validated',
    destination_section__uid=remote_entity.getUid(),
    follow_up__uid=remote_project.getUid(),
    title={'query': '_remote_%s_%s' % (local_instance.getFollowUpReference(),
                                     local_instance.getReference()),
           'key': 'ExactMatch'},
    limit=2)
  assert len(remote_instance_tree_list) == 1, "Invalid amount of Instance Tree"
  remote_user.Person_claimSlaposItemSubscription(
      reference=remote_instance_tree_list[0].getReference(), dialog_id=None,
      activate_kw=activate_kw)

remote_node.edit(
  destination_section=remote_node_change_request.getDestinationSection())

remote_node_change_request.validate()
return remote_node_change_request.invalidate(comment='Edited : %s' % remote_node.getRelativeUrl())
