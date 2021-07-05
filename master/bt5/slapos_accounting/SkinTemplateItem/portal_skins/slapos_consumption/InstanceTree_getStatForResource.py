portal = context.getPortalObject()

query_kw.update(query_kw['selection'].getParams())
start_date = query_kw.pop('start_date', None)
stop_date = query_kw.pop('stop_date', None)
software_instance_uid = query_kw.pop('software_instance', None)
instance_tree_uid = query_kw.pop('instance_tree_uid', None)

if not software_instance_uid and not instance_tree_uid:
  return ''

if start_date:
  query_kw['movement.start_date'] = dict(range='min', query=start_date)
if stop_date:
  query_kw['movement.stop_date'] = dict(range='ngt', 
                                     query=stop_date.latestTime())

if software_instance_uid and software_instance_uid != 'all':
  query_kw['aggregate_uid'] = software_instance_uid
elif instance_tree_uid and instance_tree_uid != 'all':
  query_kw['aggregate_uid'] = instance_tree_uid
elif context.getPortalType() == 'Person':
  validation_state = query_kw.pop('hosting_validation_state', 'validated')
  instance_tree_uid_list = []
  for subscription in portal.portal_catalog(
                          portal_type='Instance Tree',
                          validation_state=validation_state,
                          default_destination_section_uid=context.getUid()):
    if validation_state == 'validated' and subscription.getSlapState() == 'destroy_requested':
      continue
    if validation_state == 'archived' and subscription.getSlapState() != 'destroy_requested':
      continue
    instance_tree_uid_list.append(subscription.getUid())
  if instance_tree_uid_list:
    query_kw['aggregate_uid'] = instance_tree_uid_list
  else:
    return ''
elif context.getPortalType() in ['Software Instance', 'Instance Tree']:
  query_kw['aggregate_uid'] = context.getUid()
else:
  return ''

total_quantity = 0
for packing_list_line in portal.portal_catalog(
                    portal_type="Sale Packing List Line",
                    default_resource_uid = resource_uid,
                    **query_kw
                  ):
  total_quantity += float(packing_list_line.getQuantity())

return round(total_quantity, 3)
