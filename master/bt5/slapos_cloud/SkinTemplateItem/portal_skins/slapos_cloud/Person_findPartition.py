import random
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
person = context
portal = person.getPortalObject()

assert project_uid

compute_partition = None
query_kw = {
  'portal_type': 'Compute Partition',
  'parent__follow_up__uid': project_uid,
  'allocation_scope__uid': portal.restrictedTraverse("portal_categories/allocation_scope/open").getUid(),
}
if software_instance_portal_type == "Slave Instance":
  query_kw['free_for_request'] = 0
elif software_instance_portal_type == "Software Instance":
  query_kw['free_for_request'] = 1
  query_kw['software_release_url'] = [software_release_url, "ANY_URL"]
else:
  raise NotImplementedError("Unknown portal type %s"%
      software_instance_portal_type)

### Step 1, check where the allocation is allowed

# XXX prototype for now
tmp_instance = portal.portal_trash.newContent(
  portal_type='Instance Tree',
  temp_object=1,
  url_string=software_release_url,
  source_reference=software_type,
  follow_up_uid=project_uid
)

software_product, release_variation, type_variation = tmp_instance.InstanceTree_getSoftwareProduct()

if software_product is None:
  raise ValueError('No Software Product matching')

assert software_product.getFollowUpUid() == project_uid

allocation_cell_list = software_product.getFollowUpValue().Project_getSoftwareProductPredicateList(
  software_product=software_product,
  software_product_type=type_variation,
  software_product_release=release_variation,
  destination_value=context,
  predicate_portal_type='Allocation Supply Cell'
)

if not allocation_cell_list:
  raise ValueError('No Allocation Supply allowing this operation')

# Only partition with Instances from the same Instance Tree
instance_tree_partition_value_list = [sql_obj.getAggregateValue() \
    for sql_obj in context.getPortalObject().portal_catalog(
        portal_type=['Software Instance'],
        specialise__uid=instance_tree.getUid(),
    ) if ((sql_obj.getAggregateValue() is not None) and (sql_obj.getUrlString() == software_release_url) and (sql_obj.getSourceReference() == software_type))
]

# Get the list of allowed Compute Node, Instance Node
compute_node_list_list = [(x.getParentValue().getParentValue().getAggregateValueList(), x.getParentValue().getParentValue().isSlaveOnSameInstanceTreeAllocable()) for x in allocation_cell_list]
parent_uid_list = []
partition_uid_list = []
for compute_node_list, is_slave_on_same_instance_tree_allocable in compute_node_list_list:
  for compute_node in compute_node_list:
    if compute_node.getPortalType() == 'Compute Node':
      parent_uid_list.append(compute_node.getUid())
      if is_slave_on_same_instance_tree_allocable:
        partition_uid_list.extend([x.getUid() for x in instance_tree_partition_value_list if (x.getParentValue().getUid() == compute_node.getUid())])

    elif compute_node.getPortalType() == 'Instance Node':
      shared_instance = compute_node.getSpecialiseValue(portal_type='Software Instance')
      if (shared_instance is not None):
        # No need to search for original software type/url
        #query_kw['software_release_url'] = software_release_url
        #query_kw['software_type'] = software_type
        shared_partition = shared_instance.getAggregateValue(portal_type='Compute Partition')
        if shared_partition is not None:
          partition_uid_list.append(shared_partition.getUid())

    elif compute_node.getPortalType() == 'Remote Node':
      parent_uid_list.append(compute_node.getUid())
      # This is the only hardcoded partition accepting any slave instance allocation
      shared_partition = compute_node.restrictedTraverse('SHARED_REMOTE', None)
      if shared_partition is not None:
        partition_uid_list.append(shared_partition.getUid())

    else:
      raise NotImplementedError('Unsupported Node type: %s' % compute_node.getPortalType())

if len(parent_uid_list) == 0:
  # Ensure nothing will be found
  parent_uid_list.append(-1)
if len(partition_uid_list) == 0:
  # Ensure nothing will be found
  partition_uid_list.append(-1)

if software_instance_portal_type == "Slave Instance":
  query_kw['uid'] = partition_uid_list
elif software_instance_portal_type == "Software Instance":
  query_kw['parent_uid'] = parent_uid_list

# Explicit location
if "computer_guid" in filter_kw:
  query_kw["parent_reference"] = SimpleQuery(parent_reference=filter_kw.pop("computer_guid"))

if "instance_guid" in filter_kw:
  instance_guid = filter_kw.pop("instance_guid")
  query_kw["aggregate_related_reference"] = SimpleQuery(aggregate_related_reference=instance_guid)

if 'network_guid' in filter_kw:
  network_guid = filter_kw.pop('network_guid')
  query_kw["default_subordination_reference"] = SimpleQuery(default_subordination_reference=network_guid)

if 'project_guid' in filter_kw:
  # This is kept for compatibility for instance trees containing such parameter
  # If the reference does not match the project_uid, it will never be allocated
  query_kw['parent__follow_up__reference'] = filter_kw.pop("project_guid")

if computer_network_query:
  if query_kw.get("default_subordination_reference"):
    query_kw["default_subordination_reference"] = ComplexQuery(
        query_kw["default_subordination_reference"],
        computer_network_query
    )
  else:
    query_kw["default_subordination_reference"] = computer_network_query

extra_item_list = ["retention_delay",
                    "fw_restricted_access",
                    "fw_rejected_sources",
                    "fw_authorized_sources"]
for item in extra_item_list:
  if item in filter_kw:
    filter_kw.pop(item)

compute_node_base_category_list = [
  'group',
  'cpu_core',
  'cpu_frequency',
  'cpu_type',
  'local_area_network_type',
  'region',
  'memory_size',
  'memory_type',
  'storage_capacity',
  'storage_interface',
  'storage_redundancy',
]
for base_category in compute_node_base_category_list:
  if base_category in filter_kw:
    category_relative_url = "%s" % filter_kw.pop(base_category)
    # XXX Small protection to prevent entering strange strings
    category = context.getPortalObject().portal_categories[base_category].restrictedTraverse(str(category_relative_url), None)
    if category is None:
      query_kw["uid"] = "-1"
    else:
      query_kw["%s__uid" % base_category] = category.getUid()

if 'capability' in filter_kw:
  capability = filter_kw.pop('capability')
  query_kw['subject'] = {'query': capability, 'key': 'ExactMatch'}

if filter_kw.keys():
  # XXX Drop all unexpected keys
  query_kw["uid"] = "-1"

if test_mode:
  return bool(len(context.portal_catalog(limit=1, **query_kw)))

SQL_WINDOW_SIZE = 50

# fetch at mot 50 random Compute Partitions, and check if they are ok
isTransitionPossible = portal.portal_workflow.isTransitionPossible
result_count = portal.portal_catalog.countResults(**query_kw)[0][0]
offset = max(0, result_count-1)
if offset >= SQL_WINDOW_SIZE:
  limit = (random.randint(0, offset), SQL_WINDOW_SIZE)
else:
  limit = (0, SQL_WINDOW_SIZE)

for compute_partition_candidate in portal.portal_catalog(
                                         limit=limit, **query_kw):
  compute_partition_candidate = compute_partition_candidate.getObject()

  if compute_partition_candidate.getParentValue().getCapacityScope() == "close":
    # The compute_node was closed on this partition, so skip it.
    continue

  compute_node = compute_partition_candidate.getParentValue()
  if compute_node.getPortalType() == 'Compute Node':
    subscription_state = compute_node.Item_getSubscriptionStatus()
    if subscription_state in ('not_subscribed', 'nopaid'):
      continue
    elif subscription_state in ('subscribed', 'todestroy'):
      pass

  if software_instance_portal_type == "Software Instance":
    # Check if the compute partition can be marked as busy
    if isTransitionPossible(compute_partition_candidate, 'mark_busy'):
      compute_partition = compute_partition_candidate
      compute_partition.markBusy()
      break
  elif compute_partition_candidate.getSlapState() == "busy":
    # Only assign slave instance on busy partition
    compute_partition = compute_partition_candidate
    break

if compute_partition is None:
  raise ValueError('It was not possible to find free Compute Partition')

# lock compute partition
compute_partition.serialize()

return compute_partition.getRelativeUrl()
