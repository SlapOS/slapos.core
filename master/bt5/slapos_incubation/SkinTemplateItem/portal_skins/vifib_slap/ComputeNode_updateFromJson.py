if context.getPortalType() != 'Compute Node':
  raise TypeError('%s is not Compute Node' % context.getPath())

isTransitionPossible = context.getPortalObject().portal_workflow.isTransitionPossible
def updatePartitionList(compute_node, partition_list):
  existing_partition_dict = {}
  for c in context.contentValues():
    existing_partition_dict[c.getReference()] = c
  for partition_dict in partition_list:
    partition = existing_partition_dict.get(partition_dict['title'])
    if partition is None:
      partition = compute_node.newContent(portal_type='Compute Partition', reference=partition_dict['title'])
    if isTransitionPossible(partition, 'validate'):
      partition.validate()
    if isTransitionPossible(partition, 'mark_free'):
      partition.markFree()
    if partition.getDefaultNetworkAddressIpAddress() != partition_dict['public_ip']:
      partition.setDefaultNetworkAddressIpAddress(partition_dict['public_ip'])
    if partition.getDefaultNetworkAddressNetworkInterface() != partition_dict['tap_interface']:
      partition.setDefaultNetworkAddressNetworkInterface(partition_dict['tap_interface'])
    to_delete_list = []
    private_set = False
    for address in partition.contentValues(portal_type='Internet Protocol Address'):
      if address.getIpAddress() == partition_dict['public_ip']:
        continue
      if not private_set and address.getIpAddress() == partition_dict['private_ip']:
        if address.getNetworkInterface() != partition_dict['tap_interface']:
          address.setNetworkInterface(partition_dict['tap_interface'])
        private_set = True
        continue
      to_delete_list.append(address)
    if not private_set:
      if len(to_delete_list):
        address = to_delete_list.pop()
      else:
        address = partition.newContent(portal_type='Internet Protocol Address')
      address.setIpAddress(partition_dict['private_ip'])
      address.setNetworkInterface(partition_dict['tap_interface'])
    partition.deleteContent([q.getId() for q in to_delete_list])

def updateSoftwareList(compute_node, software_list):
  for software_dict in software_list:
    status = software_dict['status']
    try:
      if status == 'installed':
        compute_node.stopSoftwareReleaseInstallation(software_release_url=software_dict['software_release'], comment=software_dict['log'])
      elif status == 'uninstalled':
        compute_node.cleanupSoftwareReleaseInstallation(software_release_url=software_dict['software_release'], comment=software_dict['log'])
      elif status == 'error':
        compute_node.reportSoftwareReleaseInstallationError(software_release_url=software_dict['software_release'], comment=software_dict['log'])
    except ValueError:
      # BBB: Underlying code is state based, does not support multiple information
      pass

if 'partition' in compute_node_json:
  updatePartitionList(context, compute_node_json['partition'])

if 'software' in compute_node_json:
  updateSoftwareList(context, compute_node_json['software'])
