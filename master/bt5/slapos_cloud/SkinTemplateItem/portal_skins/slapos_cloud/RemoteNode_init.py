portal = context.getPortalObject()

reference = "REMOTE-%s" % portal.portal_ids.generateNewId(
    id_group='slap_instance_node_reference',
    id_generator='uid', default=1)

# XXX format
partition = context.newContent(
  portal_type='Compute Partition',
  reference='shared_partition',
  id='SHARED_REMOTE'
)
partition.markFree()
partition.markBusy()
partition.validate()

context.edit(reference=reference)
