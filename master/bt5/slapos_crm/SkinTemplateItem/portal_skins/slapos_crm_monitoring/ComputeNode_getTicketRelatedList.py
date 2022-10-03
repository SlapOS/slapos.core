"""
  Get all related tickets from the computer and everything that was allocated
  on it. 
"""
portal = context.getPortalObject()
uid_list = [context.getUid()]

computer_partition_uid_list = [
  cp.getUid() for cp in context.contentValues(portal_type="Compute Partition") if cp.getSlapState() == 'busy']

if computer_partition_uid_list:
  for instance in portal.portal_catalog(
    portal_type="Software Instance",
    select_dict={'specialise_uid': None},
    specialise_portal_type="Instance Tree",
    default_aggregate_uid=computer_partition_uid_list):

    if instance.specialise_uid not in uid_list:
      uid_list.append(instance.specialise_uid)

kw['default_or_child_aggregate_uid'] = uid_list
return context.Base_getOpenRelatedTicketList(**kw)
