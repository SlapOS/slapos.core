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

software_release_list = []
software_release_uid_dict = {}
instance_tree_url_string = instance_tree.getUrlString()

for allocation_cell in allocation_cell_list:
  software_release = allocation_cell.getSoftwareReleaseValue()
  if (software_release.getUrlString() != instance_tree_url_string):
    # Do not return duplicated release values
    software_release_uid = software_release.getUid()
    if software_release_uid not in software_release_uid_dict:
      software_release_uid_dict[software_release_uid] = None
      software_release_list.append(software_release)

return software_release_list
