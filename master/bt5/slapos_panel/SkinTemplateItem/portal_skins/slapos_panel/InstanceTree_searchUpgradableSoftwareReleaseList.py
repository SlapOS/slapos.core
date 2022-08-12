instance_tree = context

software_product, _, software_type = instance_tree.InstanceTree_getSoftwareProduct()
if software_product is None:
  # No way to upgrade, if we can find which Software Product to upgrade
  return []

# Search if the product with the same type
# XXX search only for the main node
allocation_cell_list = software_product.getFollowUpValue().Project_getSoftwareProductPredicateList(
  software_product=software_product,
  software_product_type=software_type,
  predicate_portal_type='Allocation Supply Cell'
)

return [x.getSoftwareReleaseValue() for x in allocation_cell_list if (x.getSoftwareReleaseValue().getUrlString() != instance_tree.getUrlString())]
