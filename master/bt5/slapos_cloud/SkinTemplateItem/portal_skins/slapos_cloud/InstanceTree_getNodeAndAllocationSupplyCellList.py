from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

allocation_cell_list = []
instance_tree = context
compute_node = None
root_instance = None
root_instance_list = [
  q for q in instance_tree.getSuccessorValueList(portal_type=["Software Instance", "Slave Instance"])
  if q.getSlapState() != 'destroy_requested']
if len(root_instance_list) == 1:
  root_instance = root_instance_list[0]
  partition = root_instance.getAggregateValue()
  if partition is not None:
    compute_node = partition.getParentValue()

    if (root_instance.getPortalType() == 'Slave Instance'):
      if (compute_node.getPortalType() == 'Compute Node'):
        # Search the instance node linked to this partition
        soft_instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
        if soft_instance is None:
          return (None, allocation_cell_list)
        instance_node = soft_instance.getSpecialiseRelatedValue(portal_type='Instance Node')
        if instance_node is None:
          return (None, allocation_cell_list)
        compute_node = instance_node
      elif (compute_node.getPortalType() != 'Remote Node'):
        return (None, allocation_cell_list)

if software_product is None:
  return (compute_node, allocation_cell_list)

person = context.getDestinationSectionValue(checked_permission='Access contents information')

# Search if the product with the same type
# Search only for the main node
allocation_cell_list = software_product.getFollowUpValue().Project_getSoftwareProductPredicateList(
  software_product=software_product,
  software_product_type=software_type,
  software_product_release=software_release,
  destination_value=person,
  node_value=compute_node,
  predicate_portal_type='Allocation Supply Cell'
)

if (compute_node is None) and (root_instance is not None):
  # Do not upgrade if there is no instance yet
  allocation_cell_node_list = [(x, [y.getPortalType() for y in x.getParentValue().getParentValue().getAggregateValueList()]) for x in allocation_cell_list]
  if (root_instance.getPortalType() == 'Slave Instance'):
    allocation_cell_list = [x for x, y in allocation_cell_node_list if ("Remote Node" in y) or ("Instance Node" in y)]
  elif (root_instance.getPortalType() == 'Software Instance'):
    allocation_cell_list = [x for x, y in allocation_cell_node_list if ("Remote Node" in y) or ("Compute Node" in y)]

# Remove duplicated allocation cells
# ie, multiple allocation cells matching the same release/type/node
software_release_uid_dict = {}
not_duplicated_allocation_cell_list = []
for allocation_cell in allocation_cell_list:
  # Do not return duplicated release values
  software_release_uid = allocation_cell.getSoftwareReleaseValue().getUid()
  if software_release_uid not in software_release_uid_dict:
    software_release_uid_dict[software_release_uid] = None
    not_duplicated_allocation_cell_list.append(allocation_cell)
allocation_cell_list = not_duplicated_allocation_cell_list

return (compute_node, allocation_cell_list)
