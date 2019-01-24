computer = context
# XXX: Temporary?
if computer.getAllocationScope() not in ['open/public']:
  return 0

portal = context.getPortalObject()
software_release = context.REQUEST.get('here')
if software_release is None or software_release.portal_type != 'Software Release':
  software_release = portal.portal_catalog.getResultValue(
    portal_type='Software Release',
    url_string=software_release_url,
  )

software_release_capacity = software_release.SoftwareRelease_getCapacity()
computer_free_capacity = computer.getFreeCapacityQuantity()

computer_instance_capacity = computer_free_capacity // software_release_capacity

# If computer capacity is 0, it means infinite
# In this case, only the partition count will be counted
if computer.getCapacityQuantity() == 0:
  computer_instance_capacity = float('inf')

computer_free_partition_count = portal.portal_catalog.countResults(
  parent_uid=computer.getUid(),
  software_release_url=software_release.getUrlString(),
  free_for_request=1,
)[0][0]

free_instance_count = min(
  computer_free_partition_count,
  computer_instance_capacity
)

return free_instance_count
