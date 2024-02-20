from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
compute_node = context

if compute_node.getAllocationScope() != "close/forever":
  raise ValueError("You cannot call this script on a non Close Forever computer %s" % compute_node.getRelativeUrl())

compute_partition_uid_list = [i.getUid() for i in context.objectValues(portal_type="Compute Partition")]
if not len(compute_partition_uid_list):
  context.invalidate(comment='Compute Node has no compute partition.')
  return

if compute_partition_uid_list:
  instance_list = portal.portal_catalog(
    portal_type=['Software Instance', 'Slave Instance'],
    aggregate__uid=compute_partition_uid_list,
    limit=1
  )
  if len(instance_list) == 0:
    context.invalidate(comment='Compute Node has no used compute partition.')
