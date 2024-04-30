portal = context.getPortalObject()
instance = context
project = instance.getFollowUpValue()
instance_tree = instance.getSpecialiseValue()
customer_person = instance_tree.getDestinationSection()

node_list = []

tmp_instance_tree = portal.portal_trash.newContent(
  portal_type='Instance Tree',
  temp_object=1,
  url_string=instance.getUrlString(),
  source_reference=instance.getSourceReference(),
  follow_up_value=project
)
software_product, release_variation, type_variation = tmp_instance_tree.InstanceTree_getSoftwareProduct()

if software_product is None:
  return []

allocation_cell_list = project.Project_getSoftwareProductPredicateList(
  software_product=software_product,
  software_product_type=type_variation,
  software_product_release=release_variation,
  destination_value=customer_person,
  predicate_portal_type='Allocation Supply Cell'
)

for allocation_cell in allocation_cell_list:
  allocation_supply = allocation_cell.getParentValue().getParentValue()
  node_list.extend(allocation_supply.getAggregateList())

node_list = [portal.restrictedTraverse(x) for x in list(set(node_list))]

return node_list
