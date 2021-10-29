from DateTime import DateTime
import json
portal = context.getPortalObject()
from Products.ERP5Type.Document import newTempBase

public_category_uid = portal.restrictedTraverse(
  "portal_categories/allocation_scope/open/public", None).getUid()

friend_category_uid = portal.restrictedTraverse(
  "portal_categories/allocation_scope/open/friend", None).getUid()

personal_category_uid = portal.restrictedTraverse(
  "portal_categories/allocation_scope/open/personal", None).getUid()


l = []

show_all = False
if "show_all" in kw:
  show_all = kw.pop("omit_zero_ticket")

memcached_dict = context.getPortalObject().portal_memcached.getMemcachedDict(
  key_prefix='slap_tool',
  plugin_path='portal_memcached/default_memcached_plugin')

def checkForError(reference):
  try:
    d = memcached_dict[reference]
  except KeyError:
    return 1

  d = json.loads(d)
  result = d['text']
  #last_contact = DateTime(d.get('created_at'))

  # Optimise by checking memcache information first.
  if result.startswith('#error '):
    return 1



for compute_node in portal.portal_catalog(
  default_allocation_scope_uid = [personal_category_uid, public_category_uid, friend_category_uid],
  select_list={"reference": None},
  **kw):

  uid_list = [compute_node.getUid()]
  compute_partition_uid_list = [cp.uid for cp in compute_node.searchFolder(portal_type="Compute Partition")]

  instance_count = 0
  instance_error_count = 0
  if compute_partition_uid_list:
    for instance in portal.portal_catalog(
        portal_type="Software Instance",
        select_list={"specialise_uid" : None, "reference": None},
        default_aggregate_uid=compute_partition_uid_list):
      instance_count += 1
      if instance.specialise_uid is not None:
        uid_list.append(instance.specialise_uid or compute_node.getUid())
      if checkForError(instance.reference) is not None:
        instance_error_count += 1


  related_ticket_quantity = portal.portal_catalog.countResults(
                                portal_type='Support Request',
                                simulation_state=["validated", "suspended"],
                                default_aggregate_uid=uid_list)[0][0]


  if show_all or related_ticket_quantity > 0:
    if len(compute_partition_uid_list) == 0:
      partition_use_ratio = 0
    else:
      partition_use_ratio = float(instance_count)/len(compute_partition_uid_list)
    if instance_count == 0:
      instance_error_ratio = 0
    else:
      instance_error_ratio = float(instance_error_count)/instance_count

    l.append(
       newTempBase(context, '%s'% compute_node.id, **{"title": compute_node.title,
                                                 "uid": "%s_%s" % (compute_node.getUid(), instance_count),
                                                 "reference": compute_node.reference,
                                                 "partition_use_ratio": partition_use_ratio,
                                                 "partition_use_percentage": "%.2f%%" % (partition_use_ratio*100),
                                                 "capacity_scope": compute_node.getCapacityScopeTitle(),
                                                 "instance_error_ratio": instance_error_ratio,
                                                 "instance_error_percentage": "%.2f%%" %  (instance_error_ratio*100),
                                                 "instance_quantity": instance_count,
                                                 "instance_error_quantity": instance_error_count,
                                                 "partition_quantity": len(compute_partition_uid_list),
                                                 "ticket_quantity": related_ticket_quantity }))

l.sort(key=lambda obj: obj.instance_error_ratio, reverse=True)

return l
