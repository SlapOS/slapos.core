compute_node = context.JSONRPCService_getObjectFromData(data_dict)

def compareAndUpdateAddressList(partition, partition_ip_list):
  to_delete_ip_id_list = []
  to_add_ip_dict_list = partition_ip_list[:]
  existing_address_list = partition.contentValues(portal_type='Internet Protocol Address')
  existing_address_list.sort(key=lambda x: {0: 1, 1: 2}[int(x.id == 'default_network_interface')])
  for internet_protocol_address in existing_address_list:
    current_dict = {
      "ip-address": internet_protocol_address.getIpAddress(),
      "network-interface": internet_protocol_address.getNetworkInterface(''),
    }
    if internet_protocol_address.getGatewayIpAddress(''):
      current_dict["gateway-ip-address"] = internet_protocol_address.getGatewayIpAddress('')
    if internet_protocol_address.getNetmask(''):
      current_dict["netmask"] = internet_protocol_address.getNetmask('')
    if internet_protocol_address.getNetworkAddress(''):
      current_dict["network-address"] = internet_protocol_address.getNetworkAddress('')
    if current_dict in to_add_ip_dict_list:
      to_add_ip_dict_list.remove(current_dict)
    else:
      to_delete_ip_id_list.append(internet_protocol_address.getId())

  for address in to_add_ip_dict_list:
    if to_delete_ip_id_list:
      address_document = partition.restrictedTraverse(
        to_delete_ip_id_list.pop()
      )
    else:
      kw = {'portal_type': 'Internet Protocol Address'}
      if not len(partition.objectIds(portal_type='Internet Protocol Address')):
        kw.update(id='default_network_address')
      address_document = partition.newContent(**kw)
    edit_kw = {
      "ip_address": address['ip-address'],
      "network_interface": address.get("network-interface"),
      "netmask": address.get('netmask'),
    }
    if "network-address" in address:
      edit_kw["network_address"] = address["network-address"]
    if "gateway-ip-address" in address:
      edit_kw["gateway_ip_address"] = address["gateway-ip-address"]
    address_document.edit(**edit_kw)
  if to_delete_ip_id_list:
    partition.deleteContent(to_delete_ip_id_list)

# Getting existing partitions
existing_partition_dict = {}
for c in compute_node.contentValues(portal_type="Compute Partition"):
  existing_partition_dict[c.getReference()] = c

# update compute_node data
edit_kw = {}
quantity = len(data_dict.get('compute_partition_list', []))
if compute_node.getQuantity() != quantity:
  edit_kw['quantity'] = quantity

if edit_kw:
  compute_node.edit(**edit_kw)

expected_partition_dict = {}
for send_partition in data_dict.get('compute_partition_list', []):
  partition = existing_partition_dict.get(send_partition['partition_id'], None)
  expected_partition_dict[send_partition['partition_id']] = True
  if partition is None:
    partition = compute_node.newContent(portal_type='Compute Partition')
    partition.validate()
    partition.markFree()
  elif partition.getSlapState() == 'inactive':
    # Reactivate partition
    partition.markFree(comment="Reactivated by slapformat")

  if partition.getValidationState() == "invalidated":
    partition.validate(comment="Reactivated by slapformat")
  if partition.getReference() != send_partition['partition_id']:
    partition.edit(reference=send_partition['partition_id'])

  send_capability_list = send_partition.get('capability_list') or []
  if partition.getSubjectList() != send_capability_list:
    partition.edit(subject=send_capability_list)

  compareAndUpdateAddressList(partition, send_partition.get("ip_list", []))

# Desactivate all other partitions
if 'compute_partition_list' in data_dict:
  for key, value in existing_partition_dict.items():
    if key not in expected_partition_dict:
      if value.getSlapState() == "free":
        value.markInactive(comment="Desactivated by slapformat")
      if value.getValidationState() == "validated":
        value.invalidate(comment="Desactivated by slapformat")

return {
  #"$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "compute_node_id": compute_node.getReference(),
  "date": DateTime().ISO8601(),
  "portal_type": "Compute Node",
  "success": "Done"
}
