portal = context.getPortalObject()
compute_partition = context
error_dict = {}

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
    default_source_reference=instance.getSourceReference(),
    url_string=instance.getUrlString())

  software_product, software_release, software_type = instance_tree_context.InstanceTree_getSoftwareProduct()
  if software_product is None:
    if instance.getRelativeUrl() not in error_dict:
      error_dict[instance.getRelativeUrl()] = {'instance': instance}
    message = 'No Software Product matching for: %s' % instance.getTitle()
    error_dict[instance.getRelativeUrl()]['allocation_supply_error'] = message
    continue

  project = instance.getFollowUpValue()
  assert project is not None, 'Project is None'

  person = instance_tree.getDestinationSectionValue()
  allocation_cell_list = project.Project_getSoftwareProductPredicateList(
    software_product=software_product,
    software_product_type=software_type,
    software_product_release=software_release,
    destination_value=person,
    node_value=compute_node,
    predicate_portal_type='Allocation Supply Cell'
  )
  if not allocation_cell_list:
    if instance.getRelativeUrl() not in error_dict:
      error_dict[instance.getRelativeUrl()] = {'instance': instance}
    message = 'No Allocation Supply for: %s' % instance.getTitle()
    error_dict[instance.getRelativeUrl()]['allocation_supply_error'] = message

return error_dict
