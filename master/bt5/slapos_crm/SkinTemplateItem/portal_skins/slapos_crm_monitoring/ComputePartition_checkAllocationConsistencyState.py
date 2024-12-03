portal = context.getPortalObject()
compute_partition = context
error_dict = {}
if known_error_dict is None:
  known_error_dict = {}

compute_node = compute_partition.getParentValue()
assert compute_node.getPortalType() in ['Compute Node', 'Remote Node']

instance_list = compute_partition.getAggregateRelatedValueList(portal_type=[
  'Software Instance', 'Slave Instance'])

for instance in instance_list:
  if instance.getValidationState() != 'validated' or \
      instance.getSlapState() == 'destroy_requested':
    # Outdated catalog or instance under garbage collection,
    # we skip for now.
    continue

  instance_software_release_url = instance.getUrlString()
  instance_software_type = instance.getSourceReference()

  for _e_dict in [error_dict, known_error_dict]:
    if instance_software_release_url in _e_dict:
      if instance_software_type in _e_dict[instance_software_release_url]:
        # Skip calculate same thing again?
        continue

  # Now check allocation supply consistency
  instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")

  # if there is an ongoing upgrade decision, skip, since there is already
  # a ticket for handle the inconsistency.
  if portal.portal_catalog.getResultValue(
    portal_type='Upgrade Decision',
    aggregate__uid=instance_tree.getUid(),
    simulation_state=['started', 'stopped', 'planned', 'confirmed']) is not None:
    continue

  instance_tree_context = instance_tree.asContext(
    default_source_reference=instance_software_type,
    url_string=instance_software_release_url)

  project = instance.getFollowUpValue()
  assert project is not None, 'Project is None'

  allocation_cell_list = []
  software_product, software_release, software_type = instance_tree_context.InstanceTree_getSoftwareProduct()

  if software_product is not None:
    allocation_cell_list = project.Project_getSoftwareProductPredicateList(
      software_product=software_product,
      software_product_type=software_type,
      software_product_release=software_release,
      destination_value=instance_tree.getDestinationSectionValue(),
      node_value=compute_node,
      predicate_portal_type='Allocation Supply Cell'
    )

  if not allocation_cell_list:
    # Sampling of the structure.
    # error_dict[software_release_url][software_type] = (instance, compute_partition)
    value = (instance, compute_partition)
    if instance_software_release_url not in error_dict:
      error_dict[instance_software_release_url] = {}
    if instance_software_type not in error_dict[instance_software_release_url]:
      error_dict[instance.getUrlString()][instance_software_type] = value

return error_dict
