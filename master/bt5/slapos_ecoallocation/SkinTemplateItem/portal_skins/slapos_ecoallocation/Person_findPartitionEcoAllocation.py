import random
from Products.ZSQLCatalog.SQLCatalog import SimpleQuery, ComplexQuery

compute_partition = None
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

# support SLA

# Explicit location
#explicit_location = False
if "computer_guid" in filter_kw:
  #explicit_location = True
  query_kw["parent_reference"] = SimpleQuery(parent_reference=filter_kw.pop("computer_guid"))

if "instance_guid" in filter_kw:
  #explicit_location = True
  instance_guid = filter_kw.pop("instance_guid")
  query_kw["aggregate_related_reference"] = SimpleQuery(aggregate_related_reference=instance_guid)

if 'network_guid' in filter_kw:
  network_guid = filter_kw.pop('network_guid')
  query_kw["default_subordination_reference"] = SimpleQuery(default_subordination_reference=network_guid)

if computer_network_query:
  if query_kw.get("default_subordination_reference"):
    query_kw["default_subordination_reference"] = ComplexQuery(
        query_kw["default_subordination_reference"],
        computer_network_query
    )
  else:
    query_kw["default_subordination_reference"] = computer_network_query

if "retention_delay" in filter_kw:
  filter_kw.pop("retention_delay")

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

query_kw["capacity_scope_uid"] = context.getPortalObject().portal_categories.capacity_scope.open.getUid()
# if not explicit_location:
#   # Only allocation on public compute_node
#   query_kw["allocation_scope_uid"] = context.getPortalObject().portal_categories.allocation_scope.open.public.getUid()

if filter_kw.keys():
  # XXX Drop all unexpected keys
  query_kw["uid"] = "-1"

if test_mode:
  return bool(len(context.portal_catalog(limit=1, **query_kw)))

# Get only one compute_partition per compute_node
compute_partition_list = context.portal_catalog(group_by="parent_uid", **query_kw)

software_release_list = context.portal_catalog(
  portal_type="Software Release",
  url_string=software_release_url
) 

if len(software_release_list) == 0:
  # Forbid to allocate partitions without an existing Software Release Document.
  raise KeyError(len(software_release_list))

delta_co2_contribution_list = software_release_list[0].SoftwareRelease_getDeltaCO2List(compute_partition_list)

isTransitionPossible = context.getPortalObject().portal_workflow.isTransitionPossible

while len(delta_co2_contribution_list):
  partition_candidate_list = delta_co2_contribution_list.pop(min(delta_co2_contribution_list))

  for compute_partition_candidate in partition_candidate_list:
    compute_partition_candidate = compute_partition_candidate.getObject()
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
