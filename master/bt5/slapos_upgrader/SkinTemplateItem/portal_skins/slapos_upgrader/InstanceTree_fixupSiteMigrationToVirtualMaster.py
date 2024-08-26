from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance_tree = context.getObject()

instance_tree_virtual_master = instance_tree.getFollowUpValue()
instance_tree_virtual_master_relative_url = instance_tree_virtual_master.getRelativeUrl()

#######################################################################
# If root instance is not allocated on the same virtual master than instance tree
# remove the instance tree virtual master
# and rerun the migration
#######################################################################
root_software_instance = ([x for x in instance_tree.getSuccessorValueList() if x.getTitle()==instance_tree.getTitle()] + [None])[0]
sla_xml_dict = {}
if root_software_instance is not None:
  try:
    sla_xml_dict = root_software_instance.getSlaXmlAsDict()
  except: # pylint: disable=bare-except
    # XMLSyntaxError
    pass

  root_partition = root_software_instance.getAggregateValue()
  if root_partition is not None:
    root_instance_virtual_master_relative_url = root_partition.getParentValue().getFollowUp(None)
    if ((root_instance_virtual_master_relative_url is not None) and
        (root_instance_virtual_master_relative_url != instance_tree_virtual_master_relative_url) and
        (not sla_xml_dict)):

      instance_tree_migration_needed = True

      # ensure no software instance is not on the instance tree
      # virtual master. If so, keep the instance tree virtual master
      for sql_result in portal.portal_catalog(
        specialise__uid=instance_tree.getUid(),
        portal_type='Software Instance'
      ):
        instance = sql_result.getObject()
        instance_partition = instance.getAggregateValue()
        if instance_partition is not None:
          instance_virtual_master_relative_url = instance_partition.getParentValue().getFollowUp(None)
          if (instance_virtual_master_relative_url == instance_tree_virtual_master_relative_url):
            instance_tree_migration_needed = False

      if instance_tree_migration_needed:
        edit_kw ={'follow_up_value': None}
        activate_kw = {'tag': tag}
        instance_tree.edit(**edit_kw)
        instance_tree.reindexObject(activate_kw=activate_kw)
        for sql_result in portal.portal_catalog(
          specialise__uid=instance_tree.getUid(),
          portal_type=['Software Instance', 'Slave Instance']
        ):
          instance = sql_result.getObject()
          instance.edit(**edit_kw)
          instance.reindexObject(activate_kw=activate_kw)
        return

#######################################################################
# If instance is not allocated on the same virtual master than instance tree
# create remote node
#######################################################################

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
