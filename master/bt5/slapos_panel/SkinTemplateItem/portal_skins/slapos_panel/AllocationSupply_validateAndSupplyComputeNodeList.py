from Products.ERP5Type.Message import translateString

allocation_supply = context

url_string_list = []

for allocation_supply_line in allocation_supply.contentValues(portal_type="Allocation Supply Line"):
  for allocation_supply_cell in allocation_supply_line.contentValues(portal_type="Allocation Supply Cell"):
    if allocation_supply_cell.isAllocable():
      release_variation = allocation_supply_cell.getSoftwareReleaseValue()
      if release_variation is not None and release_variation.getUrlString() not in url_string_list:
        url_string_list.append(release_variation.getUrlString())

for compute_node in allocation_supply.getAggregateValueList(portal_type="Compute Node"):
  for url_string in url_string_list:
    compute_node.requestSoftwareRelease(
      software_release_url=url_string,
      state='available'
    )

allocation_supply.validate()

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('Allocation Supply validated.')}
)
