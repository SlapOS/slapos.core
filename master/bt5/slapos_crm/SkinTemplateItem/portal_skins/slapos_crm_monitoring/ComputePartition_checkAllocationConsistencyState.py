portal = context.getPortalObject()
compute_partition = context
error_dict = {}

compute_node = compute_partition.getParentValue()
assert compute_node.getPortalType() in ['Compute Node', 'Remote Node']

instance_list = portal.portal_catalog(
  portal_type=['Software Instance', 'Slave Instance'],
  aggregate__uid=compute_partition.getUid(),
  validation_state='validated',
  group_by=['source_reference', 'url_string', 'specialise_uid', 'portal_type']
)

instance_tree_upgrade_cache = {}
software_product_cache_map = {}

for _instance in instance_list:
  # Due group by, fetch real object
  instance = _instance.getObject()
  if instance.getSlapState() == 'destroy_requested':
    # Outdated catalog or instance under garbage collection,
    # we skip for now.
    continue

  instance_software_release_url = instance.getUrlString()
  instance_software_type = instance.getSourceReference()

  # Now check allocation supply consistency
  instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")

  # Create a temporary instance tree as the instance would be the root
  # Instance.
  instance_tree_context = instance_tree.asContext(
    title=instance.getTitle(),
    default_source_reference=instance_software_type,
    url_string=instance_software_release_url)

  instance_tree_context.setSuccessorValue(instance)
  assert instance_tree_context.getSuccessorValue() == instance
  project = instance.getFollowUpValue()
  assert project is not None, 'Project is None'

  cache_key = "!!!".join([str(project.getUid()), instance_software_release_url, instance_software_type])
  if cache_key not in software_product_cache_map:
    software_product_cache_map[cache_key] = instance_tree_context.InstanceTree_getSoftwareProduct()
  software_product, software_release, software_type = software_product_cache_map[cache_key]

  if software_product is None:
    allocable_compute_node, allocation_cell_list = compute_node, []
  else:
    allocable_compute_node, allocation_cell_list = instance_tree_context.InstanceTree_getNodeAndAllocationSupplyCellList(
      software_product=software_product,
      software_release=software_release,
      software_type=software_type)
    if allocable_compute_node is None:
      # Such case occurs if a previous allocation supply
      # has been invalidated
      allocable_compute_node, allocation_cell_list = compute_node, []

  if not allocation_cell_list:
    # In case of detected issue, check if there is an upgrade decision
    if instance_tree.getUid() not in instance_tree_upgrade_cache:
      instance_tree_upgrade_cache[instance_tree.getUid()] = portal.portal_catalog.getResultValue(
      portal_type='Upgrade Decision',
      aggregate__uid=instance_tree.getUid(),
      simulation_state=['started', 'stopped', 'planned', 'confirmed']) is not None
    if instance_tree_upgrade_cache[instance_tree.getUid()]:
      continue

    # Sampling of the structure
    # error_dict = {
    #   compute_node or instance_node or remote_node : {
    #      software_release_url: {
    #        software_type: sample_instance
    #      }
    #   }
    # }
    # value = (instance, allocable_compute_node)
    allocable_compute_node_url = allocable_compute_node.getRelativeUrl()
    if allocable_compute_node_url not in error_dict:
      error_dict[allocable_compute_node_url] = {}
    if instance_software_release_url not in error_dict[allocable_compute_node_url]:
      error_dict[allocable_compute_node_url][instance_software_release_url] = {}

    if instance_software_type not in error_dict[allocable_compute_node_url][instance_software_release_url]:
      error_dict[allocable_compute_node_url][instance_software_release_url][instance_software_type] = instance

return error_dict
