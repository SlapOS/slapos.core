reference = "REMOTE-%s" % context.getId()

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
