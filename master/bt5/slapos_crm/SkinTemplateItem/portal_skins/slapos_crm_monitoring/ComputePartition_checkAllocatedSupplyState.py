compute_partition = context

compute_node = compute_partition.getParentValue()
assert compute_node.getPortalType() == 'Compute Node'

instance = compute_partition.getAggregateRelatedValue(portal_type='Software Instance')
assert instance is not None, 'Instance is None'
assert instance.getValidationState() != 'validated', 'Instance is invalid'

project = instance.getFollowUpValue()
assert project is not None, 'Project is None'

instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")
instance_tree_context = instance_tree.asContext(
  source_reference=instance.getSourceReference(),
  url_string=instance.getUrlString()
)

software_product, software_release, software_type = instance_tree_context.InstanceTree_getSoftwareProduct()
if software_product is None:
  return 'No Software Product matching'

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
  return 'No Allocation Supply'
