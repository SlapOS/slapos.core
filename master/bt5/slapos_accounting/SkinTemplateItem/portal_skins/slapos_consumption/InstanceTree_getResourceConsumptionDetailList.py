from DateTime import DateTime
from Products.ERP5Type.Document import newTempBase

portal = context.getPortalObject()

start_date = query_kw.pop('start_date', None)
stop_date = query_kw.pop('stop_date', None)
software_instance_uid = query_kw.pop('software_instance', None)
instance_tree_uid = query_kw.pop('instance_tree_uid', None)
resource_uid = query_kw.pop('resource_service', None)
comparison_operator = query_kw.pop('resource_operator', None)
resource_value = query_kw.pop('resource_value', None)

if not software_instance_uid and not instance_tree_uid:
  return []

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
  validation_state = query_kw.pop('hosting_validation_state', None)
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
    return []
elif context.getPortalType() in ['Software Instance', 'Instance Tree',
                                  'Compute Node']:
  query_kw['aggregate_uid'] = context.getUid()
else:
  return []

cpu_resource_uid = context.service_module.cpu_load_percent.getUid()
memory_resource_uid = context.service_module.memory_used.getUid()
disk_resource_uid = context.service_module.disk_used.getUid()
resource_uid_list = [cpu_resource_uid, memory_resource_uid, disk_resource_uid]
if resource_uid and comparison_operator and resource_value:
  resource_uid_list = [resource_uid]
  query_kw['quantity'] = dict(quantity=resource_value, range=comparison_operator)

consumption_dict = {}

def getPackingListLineForResource(resource_uid_list):
  return portal.portal_catalog(
    portal_type="Sale Packing List Line",
    default_resource_uid = resource_uid_list,
    **query_kw
  )

def setDetailLine(packing_list_line):
  start_date = DateTime(packing_list_line.getStartDate()).strftime('%Y/%m/%d')
  hosting_s = packing_list_line.getAggregateValue(
                                            portal_type='Instance Tree')
  software_instance = packing_list_line.getAggregateValue(
                                            portal_type='Software Instance')
  compute_partition = packing_list_line.getAggregateValue(
                                            portal_type='Compute Partition')
  if software_instance is None:
    # In case we found SPL line not aggregated to instance and hosting
    return
  instance_tree_reference = hosting_s.getReference()
  instance_reference = software_instance.getReference()
  compute_node_title = ""
  if compute_partition is not None:
    compute_node = compute_partition.getParent()
    compute_node_title = compute_node.getTitle() if compute_node.getCpuCore() is None else '%s (%s CPU Cores)' % (compute_node.getTitle(), compute_node.getCpuCore())
  #default_line = {'date': {'hosting_ref': ['hs_title', {'instance_ref': ['inst_title', ['res1', 'res2', 'resN'] ] } ] } }
  if not start_date in consumption_dict:
    # Add new date line
    consumption_dict[start_date] = {instance_tree_reference: 
                                      [hosting_s.getTitle(), 
                                        {instance_reference: 
                                          [software_instance.getTitle(), 
                                            [0.0, 0.0, 0.0],
                                            software_instance.getRelativeUrl(),
                                            compute_node_title
                                          ]
                                        },
                                        hosting_s.getRelativeUrl()
                                      ]
                                    }
  # Add new Hosting line
  if not instance_tree_reference in consumption_dict[start_date]:
    consumption_dict[start_date][instance_tree_reference] = [hosting_s.getTitle(),
                                                        {instance_reference: 
                                                          [software_instance.getTitle(), 
                                                            [0.0, 0.0, 0.0],
                                                            software_instance.getRelativeUrl(),
                                                            compute_node_title
                                                          ]
                                                        },
                                                        hosting_s.getRelativeUrl()
                                                      ]
  # Add new instance line
  if not instance_reference in consumption_dict[start_date][instance_tree_reference][1]:
    consumption_dict[start_date][instance_tree_reference][1][instance_reference] = [
        software_instance.getTitle(),  [0.0, 0.0, 0.0], software_instance.getRelativeUrl(),
        compute_node_title
      ]
  if packing_list_line.getResourceUid() == cpu_resource_uid:
    quantity = round(float(packing_list_line.getQuantity()), 3)
    consumption_dict[start_date][instance_tree_reference][1][instance_reference][1][0] = quantity
  elif packing_list_line.getResourceUid() == memory_resource_uid:
    quantity = round( float(packing_list_line.getQuantity()), 3)
    consumption_dict[start_date][instance_tree_reference][1][instance_reference][1][1] = quantity
  elif packing_list_line.getResourceUid() == disk_resource_uid:
    quantity = round( float(packing_list_line.getQuantity()), 3)
    consumption_dict[start_date][instance_tree_reference][1][instance_reference][1][2] = quantity

# Add CPU_LOAD consumption details
for packing_list_line in getPackingListLineForResource(resource_uid_list):
  setDetailLine(packing_list_line)

consumption_list = []
i = 1
# Sort on movement.start_date in catalog doesn't work !
for date in sorted(consumption_dict, reverse=True):
  for hosting_key in sorted(consumption_dict[date]):
    instance_tree_title, instance_dict, hs_url = consumption_dict[date][hosting_key]
    for instance_value_list in instance_dict.values():
      instance_title, values, instance_url, compute_node_title = instance_value_list
      line = newTempBase(portal, instance_url, uid="%s_%s" % (context.getUid(), i))
      line.edit(
        title=instance_tree_title,
        start_date=date,
        instance_title=instance_title,
        cpu_load=values[0],
        memory_used=values[1],
        disk_used=values[2],
        compute_node_title=compute_node_title,
        hosting_url=hs_url,
        instance_url=instance_url
      )
      consumption_list.append(line)
      i += 1

return consumption_list
