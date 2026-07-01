from Products.ERP5Type.Message import translateString

allocation_supply = context

url_string_list = []
allocation_supply_line_to_delete_id_list = []

for allocation_supply_line in allocation_supply.contentValues(portal_type="Allocation Supply Line"):
  is_allocable = False
  for allocation_supply_cell in allocation_supply_line.contentValues(portal_type="Allocation Supply Cell"):
    if allocation_supply_cell.isAllocable():
      is_allocable = True
      release_variation = allocation_supply_cell.getSoftwareReleaseValue()
      if release_variation is not None and release_variation.getUrlString() not in url_string_list:
        url_string_list.append(release_variation.getUrlString())
  if not is_allocable:
    # Delete the line to improve visible of the supply logic
    allocation_supply_line_to_delete_id_list.append(allocation_supply_line.getId())

for compute_node in allocation_supply.getAggregateValueList(portal_type="Compute Node"):
  for url_string in url_string_list:
    compute_node.requestSoftwareRelease(
      software_release_url=url_string,
      state='available'
    )

allocation_supply.validate()

if allocation_supply_line_to_delete_id_list:
  # Delete the lines to improve visible of the supply logic
  allocation_supply.manage_delObjects(allocation_supply_line_to_delete_id_list)

consistency_list = allocation_supply.checkConsistency()
if len(consistency_list) != 0:
  # immediately invalidate to generate all possible lines
  allocation_supply.AllocationSupply_invalidateComputeNodeList(batch=1)
  return allocation_supply.Base_redirect(keep_items={
    'portal_status_level': 'error',
    'portal_status_message': str(consistency_list[0].getMessage())
  })

return allocation_supply.Base_redirect(
  keep_items={'portal_status_message': translateString('Allocation Supply validated.')}
)
