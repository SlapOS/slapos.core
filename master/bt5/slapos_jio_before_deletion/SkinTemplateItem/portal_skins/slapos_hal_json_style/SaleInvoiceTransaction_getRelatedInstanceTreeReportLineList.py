aggregated_reference = context.getCausalityReferenceList(portal_type='Sale Packing List', checked_permission='View')
from Products.ERP5Type.Document import newTempBase
from DateTime import DateTime

portal = context.getPortalObject()
if not aggregated_reference:
  return []

item_dict = []
for line in portal.portal_catalog(portal_type='Sale Packing List Line',
                                   grouping_reference=aggregated_reference,
                                   default_resource_uid=-1,#portal.service_module.slapos_instance_subscription.getUid(),
                                   sort_on=[('default_aggregate_uid', 'ASC'), ('movement.start_date', 'ASC')]):

  item_relative_url = line.getAggregate(portal_type='Instance Tree')
  if not item_relative_url:
    continue

  item_title = line.getAggregateTitle(portal_type='Instance Tree')
  start_date = line.getStartDate()
  stop_date = line.getStopDate()
  quantity = line.getQuantity()
  item_dict.setdefault(item_relative_url, [item_title, start_date, stop_date, 0])
  item_dict.update({item_relative_url: [item_title,
                               min(item_dict[item_relative_url][1], start_date),
                               max(item_dict[item_relative_url][2], stop_date),
                               sum([item_dict[item_relative_url][3], quantity])]})

report_line_list = []
for relative_url in item_dict:
  title, start_date, stop_date, quantity = item_dict[relative_url]
  report_line_list.append(
    newTempBase(portal, relative_url,
      title=title,
      start_date=start_date,
      stop_date=stop_date,
      quantity=quantity)
  )

return report_line_list
