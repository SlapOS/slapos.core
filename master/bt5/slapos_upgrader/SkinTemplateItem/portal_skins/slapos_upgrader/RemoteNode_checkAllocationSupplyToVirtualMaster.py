from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
remote_node = context

# If there is already a related allocation supply, do nothing
if portal.portal_catalog.getResultValue(portal_type="Allocation Supply",
                                        aggregate__uid=remote_node.getUid()) is not None:
  return

product_dict = {}

for sql_partition_result in remote_node.contentValues(
  portal_type=["Compute Partition"]
):
  partition = sql_partition_result.getObject()
  if partition.getSlapState() == 'busy':

    for sql_instance_result in portal.portal_catalog(
      portal_type=["Slave Instance", "Software Instance"],
      aggregate__uid=partition.getUid(),
    ):
      software_instance = sql_instance_result.getObject()
      if software_instance.getSlapState() in ["start_requested", "stop_requested"]:
        software_product, release_variation, type_variation = software_instance.InstanceTree_getSoftwareProduct()
        if software_product is None:
          raise NotImplementedError(software_instance.getRelativeUrl())

        if software_product.getRelativeUrl() not in product_dict:
          product_dict[software_product.getRelativeUrl()] = {}
        if type_variation.getRelativeUrl() not in product_dict[software_product.getRelativeUrl()]:
          product_dict[software_product.getRelativeUrl()][type_variation.getRelativeUrl()] = set()
        product_dict[software_product.getRelativeUrl()][type_variation.getRelativeUrl()].add(release_variation.getRelativeUrl())

for slave_on_same_instance_tree_allocable, product_dict in [
  (False, product_dict)
]:
  if product_dict:
    # Time to create the allocation supply
    #print product_dict
    allocation_supply = portal.allocation_supply_module.newContent(
      title="%s %s" % (remote_node.getReference(), DateTime().rfc822()),
      portal_type="Allocation Supply",
      slave_on_same_instance_tree_allocable=slave_on_same_instance_tree_allocable,
      destination_project_value=remote_node.getFollowUpValue(),
      start_date_range_min=DateTime(),
      aggregate_value=remote_node,
      activate_kw=activate_kw
    )

    for software_product_relative_url in product_dict:
      software_product = portal.restrictedTraverse(software_product_relative_url)
      allocation_supply_line = allocation_supply.newContent(
        portal_type="Allocation Supply Line",
        title=software_product.getTitle(),
        resource_value=software_product,
        activate_kw=activate_kw
      )
      allocation_supply_line.edit(
        p_variation_base_category_list=allocation_supply_line.getVariationRangeBaseCategoryList(),
        activate_kw=activate_kw
      )
      base_id = 'path'
      allocation_supply_line.setCellRange(
        base_id=base_id,
        *allocation_supply_line.SupplyLine_asCellRange(base_id=base_id)
      )

      for type_variation_relative_url in product_dict[software_product_relative_url]:
        for release_variation_relative_url in product_dict[software_product_relative_url][type_variation_relative_url]:
          # create cells
          resource_vcl = [
            'software_release/%s' % release_variation_relative_url,
            'software_type/%s' % type_variation_relative_url
          ]
          resource_vcl.sort()
          cell_key = resource_vcl
          allocation_supply_cell = allocation_supply_line.newCell(
            base_id=base_id,
            portal_type='Allocation Supply Cell',
            *cell_key
          )
          allocation_supply_cell.edit(
            mapped_value_property_list=['allocable'],
            allocable=True,
            predicate_category_list=cell_key,
            variation_category_list=cell_key,
            activate_kw=activate_kw
          )

    allocation_supply.validate()
