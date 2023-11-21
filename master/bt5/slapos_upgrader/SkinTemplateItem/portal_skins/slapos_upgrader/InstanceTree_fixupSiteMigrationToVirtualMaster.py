from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance_tree = context.getObject()

instance_tree_virtual_master = instance_tree.getFollowUpValue()
instance_tree_virtual_master_relative_url = instance_tree_virtual_master.getRelativeUrl()

# Check recursively the instance tree
# and detect orphaned nodes
is_orphaned_instance_dict = {}
for successor in instance_tree.getSuccessorList():
  is_orphaned_instance_dict[successor] = False
for sql_result in portal.portal_catalog(specialise__uid=instance_tree.getUid()):
  instance = sql_result.getObject()
  if instance.getRelativeUrl() not in is_orphaned_instance_dict:
    is_orphaned_instance_dict[instance.getRelativeUrl()] = True
  for successor in instance.getSuccessorList():
    is_orphaned_instance_dict[successor] = False

# Then, browser the roots, and stop as soon as one with a different virtual master is found
# all its successors will be moved to if needed
instance_to_check_list = [portal.restrictedTraverse(x) for x in is_orphaned_instance_dict if is_orphaned_instance_dict[x]]
instance_to_check_list.extend(instance_tree.getSuccessorValueList())

remote_virtual_master_dict = {}
while instance_to_check_list:
  instance = instance_to_check_list.pop()
  is_consistent = True
  partition = instance.getAggregateValue()
  if partition is not None:
    instance_virtual_master_relative_url = partition.getParentValue().getFollowUp(None)
    if (instance_virtual_master_relative_url is not None) and (instance_virtual_master_relative_url != instance_tree_virtual_master_relative_url):
      if instance_virtual_master_relative_url not in remote_virtual_master_dict:
        remote_virtual_master_dict[instance_virtual_master_relative_url] = []
      remote_virtual_master_dict[instance_virtual_master_relative_url].append(instance.getRelativeUrl())
      is_consistent = False

  if is_consistent:
    # Check sub instances only if parent is ok
    instance_to_check_list.extend(instance.getSuccessorValueList())

# Trigger migration
for instance_virtual_master_relative_url in remote_virtual_master_dict:
  instance_tree_virtual_master.Project_checkSiteMigrationCreateRemoteNode(
    instance_virtual_master_relative_url,
    remote_virtual_master_dict[instance_virtual_master_relative_url],
    activate_kw={'tag': tag, 'serialization_tag': tag, 'limit': 1}
  )
