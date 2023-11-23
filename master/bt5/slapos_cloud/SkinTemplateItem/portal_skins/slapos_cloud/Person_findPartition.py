import random
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery
person = context
portal = context.getPortalObject()

def getOpenAllocationScopeUidList(exclude_uid_list):
  return [scope.getUid() for scope in portal.portal_categories.allocation_scope.open.objectValues()
           if scope.getUid() not in exclude_uid_list]


compute_partition = None
filter_kw_copy = filter_kw.copy()
query_kw = {
  'software_release_url': software_release_url,
  'portal_type': 'Compute Partition',
}
if software_instance_portal_type == "Slave Instance":
  query_kw['free_for_request'] = 0
  query_kw['software_type'] = software_type
elif software_instance_portal_type == "Software Instance":
  query_kw['free_for_request'] = 1
else:
  raise NotImplementedError("Unknown portal type %s"%
      software_instance_portal_type)

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
  # This implementation isn't optimal, as we would prefere place a direct query rather them make an
  # direct query.
  project_reference = filter_kw.pop("project_guid")

  if 'parent_reference' not in query_kw:
    # Get Compute Node list from Tracking API
    from DateTime import DateTime
    project = context.portal_catalog.getResultValue(portal_type="Project", reference=project_reference)

    if project is not None:
      query_kw["parent_reference"] = SimpleQuery(parent_reference=project.Project_getComputeNodeReferenceList())

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
      query_kw["%s_uid" % base_category] = category.getUid()

if 'capability' in filter_kw:
  capability = filter_kw.pop('capability')
  query_kw['subject'] = {'query': capability, 'key': 'ExactMatch'}

query_kw["capacity_scope_uid"] = portal.portal_categories.capacity_scope.open.getUid()
if subscription_reference is not None and software_instance_portal_type != "Slave Instance":
  # Subscriptions uses a specific set of allocation scope
  query_kw["allocation_scope_uid"] = portal.portal_categories.allocation_scope.open.subscription.getUid()
elif subscription_reference is not None and \
     software_instance_portal_type == "Slave Instance" and \
     is_root_slave:
  # Subscriptions uses a specific set of allocation scope
  query_kw["allocation_scope_uid"] = getOpenAllocationScopeUidList([])
else:
  # else pic anything but open/subscription
  query_kw["allocation_scope_uid"] = getOpenAllocationScopeUidList(
    exclude_uid_list=[portal.portal_categories.allocation_scope.open.subscription.getUid()])


extra_query_kw = context.ComputePartition_getCustomAllocationParameterDict(
      software_release_url, software_type, software_instance_portal_type,
      filter_kw_copy, computer_network_query, test_mode)

if extra_query_kw:
  query_kw.update(extra_query_kw)

if filter_kw.keys():
  # XXX Drop all unexpected keys
  query_kw["uid"] = "-1"

if test_mode:
  return bool(len(context.portal_catalog(limit=1, **query_kw)))

SQL_WINDOW_SIZE = 50

# fetch at mot 50 random Compute Partitions, and check if they are ok
isTransitionPossible = person.getPortalObject().portal_workflow.isTransitionPossible
result_count = person.portal_catalog.countResults(**query_kw)[0][0]
offset = max(0, result_count-1)
if offset >= SQL_WINDOW_SIZE:
  limit = (random.randint(0, offset), SQL_WINDOW_SIZE)
else:
  limit = (0, SQL_WINDOW_SIZE)


for compute_partition_candidate in context.portal_catalog(
                                         limit=limit, **query_kw):
  compute_partition_candidate = compute_partition_candidate.getObject()
  if compute_partition_candidate.getParentValue().getCapacityScope() == "close":
    # The compute_node was closed on this partition, so skip it.
    continue

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
