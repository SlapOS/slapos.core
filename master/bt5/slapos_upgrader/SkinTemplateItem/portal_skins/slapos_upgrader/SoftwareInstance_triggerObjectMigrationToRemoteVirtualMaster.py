from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance = context

instance_virtual_master_relative_url = instance.getFollowUp()
connection_xml = instance.getConnectionXml()

remote_node = portal.restrictedTraverse(remote_node_relative_url)
remote_partition = instance.getAggregateValue()

try:
  assert instance_virtual_master_relative_url == remote_node.getFollowUp()
  assert instance_virtual_master_relative_url != remote_node.getDestinationProject()
  assert remote_partition.getFollowUp() == remote_node.getDestinationProject()
except AssertionError:
  if remote_partition.getParentValue().getRelativeUrl() == remote_node_relative_url:
    return
  if instance_virtual_master_relative_url == remote_node.getDestinationProject():
    return
  # Something wrong here, maybe the instance was already migrated
  raise

tag = "%s_%s" % (script.id, instance.getUid())
activate_kw = {'tag': tag}
#########################################################
# Move current instance to the remote node
#########################################################
if instance.getPortalType() == 'Slave Instance':
  # All slave instances goes to this magic partition
  new_partition = remote_node.restrictedTraverse('SHARED_REMOTE')
elif instance.getPortalType() == 'Software Instance':
  new_partition = remote_node.newContent(
    portal_type="Compute Partition",
    reference="slapmigration",
  )
  new_partition.markFree()
  new_partition.validate()
  new_partition.markBusy()
else:
  raise NotImplementedError('Not supported instance type: %s' % instance.getPortalType())

portal.portal_workflow.doActionFor(instance, action='edit_action', comment="Migrated to a remote node")
instance.edit(aggregate_value=new_partition, activate_kw=activate_kw)
assert new_partition.getSlapState() == 'busy'

#########################################################
# Create a new instance tree on the remote project
#########################################################
new_partition.ComputePartition_propagateRemoteNode(local_instance_list=[instance.getRelativeUrl()])
remote_instance_tree = context.REQUEST.get('request_instance_tree')
requested_software_instance = context.REQUEST.get('request_instance')

if remote_instance_tree is None:
  assert (instance.getSlapState() == 'destroy_requested') or (instance.getValidationState() == 'invalidated')
else:
  requested_software_instance.edit(
    # keep the previous allocation partition
    aggregate_value=remote_partition,
    # keep the original connection xml
    connection_xml=connection_xml,
    activate_kw=activate_kw
  )
  instance.edit(connection_xml=connection_xml, activate_kw=activate_kw)
  assert remote_partition.getSlapState() == 'busy'

  # CDN compatibility
  # invert the instance references, to ensure cdn keep the same domain name
  # as we also want to keep subobject (login), change the instance from one tree into another
  original_predecessor = instance.getSuccessorRelatedValue()
  if original_predecessor is not None:
    successor_list = original_predecessor.getSuccessorList()
    successor_list = [x.replace(instance.getRelativeUrl(), requested_software_instance.getRelativeUrl()) for x in successor_list]

  instance_title = instance.getTitle()
  instance_tree = instance.getSpecialiseValue()

  new_remote_title = '_remote_%s_%s' % (instance_tree.getFollowUpReference(), requested_software_instance.getReference())

  remote_instance_tree.edit(
    successor_value=instance,
    title=new_remote_title,
    activate_kw=activate_kw
  )
  instance.edit(
    title=remote_instance_tree.getTitle(),
    specialise_value=remote_instance_tree,
    aggregate_value=remote_partition,
    follow_up_value=remote_instance_tree.getFollowUpValue(),
    activate_kw=activate_kw
  )
  if original_predecessor is not None:
    original_predecessor.edit(
      successor_list=successor_list,
      activate_kw=activate_kw
    )
  requested_software_instance.edit(
    title=instance_title,
    specialise_value=instance_tree,
    aggregate_value=new_partition,
    follow_up_value=instance_tree.getFollowUpValue(),
    activate_kw=activate_kw
  )

  # Change the specialise value of all successors of the new instance tree
  remote_successor_list = instance.getSuccessorValueList()
  while remote_successor_list:
    remote_successor = remote_successor_list.pop()
    remote_successor_list.extend(remote_successor.getSuccessorValueList())
    remote_successor.edit(
      specialise_value=remote_instance_tree,
      follow_up_value=remote_instance_tree.getFollowUpValue(),
      activate_kw=activate_kw
    )

  # Trigger fixup of the newly instance tree if needed
  # to continue cleaning up the remaining instances of the tree
  remote_instance_tree.activate(after_tag=tag).InstanceTree_fixupSiteMigrationToVirtualMaster()
