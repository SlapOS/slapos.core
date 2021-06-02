portal = context.getPortalObject()

# This won't work well on clusters deployed on multiple computers.
root_instance = context.getSuccessorValue(
  portal_type=["Software Instance", "Slave Instance"])
if root_instance is not None and root_instance.getPortalType() == 'Slave Instance':
  return True

# Get Computer List
instance_list = context.getSpecialiseRelatedValueList(
  portal_type="Software Instance")

computer_list = []
for instance in instance_list:
  if instance.getSlapState() == "destroy_requested":
    continue

  partition = instance.getAggregateValue(portal_type="Computer Partition")
  if partition is None:
    continue

  computer_list.append(partition.getParentValue().getUid())

if computer_list is None:
  return True

full_software_installation_list = [si for si in 
          portal.portal_catalog(
            portal_type='Software Installation',
            url_string=software_release_url,
            default_aggregate_uid=computer_list,
            validation_state='validated'
          ) if si.getSlapState() == 'start_requested']

if len(full_software_installation_list) > 0 and \
      len(full_software_installation_list) == len(set(computer_list)):
  # Software is available for the root instance
  software_installation = full_software_installation_list[0]
  message = software_installation.Base_getNewsDict(software_installation)['text']
  if message.startswith("#access"):
    return True
