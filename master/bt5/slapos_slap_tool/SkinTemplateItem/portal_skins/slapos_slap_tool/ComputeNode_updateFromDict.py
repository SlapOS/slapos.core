def compareAndUpdateAddressList(document, address_list, additional_dict=None):
  if additional_dict is None:
    additional_dict = {}
  to_delete_ip_id_list = []
  to_add_ip_dict_list = address_list[:]
  existing_address_list = document.contentValues(portal_type='Internet Protocol Address')
  existing_address_list.sort(key=lambda x: {0: 1, 1: 2}[int(x.id == 'default_network_interface')])
  for address in existing_address_list:
    current_dict = {
      'addr': address.getIpAddress(),
      'netmask': address.getNetmask()
    }
    if current_dict in to_add_ip_dict_list:
      to_add_ip_dict_list.remove(current_dict)
    else:
      # XXX - Only delete if Network interface are supposed to be the same
      if 'network_interface' in additional_dict:
        if address.getNetworkInterface('') and additional_dict['network_interface'] != address.getNetworkInterface():
          continue
      to_delete_ip_id_list.append(address.getId())

  for address in to_add_ip_dict_list:
    if to_delete_ip_id_list:
      address_document = document.restrictedTraverse(
        to_delete_ip_id_list.pop()
      )
    else:
      kw = {'portal_type': 'Internet Protocol Address'}
      if not len(document.objectIds(portal_type='Internet Protocol Address')):
        kw.update(id='default_network_address')
      address_document = document.newContent(**kw)
    address_document.edit(
      ip_address=address['addr'],
      netmask=address['netmask'],
      **additional_dict
    )
  if to_delete_ip_id_list:
    document.deleteContent(to_delete_ip_id_list)


# Getting existing partitions
existing_partition_dict = {}
for c in context.contentValues(portal_type="Compute Partition"):
  existing_partition_dict[c.getReference()] = c

# update compute_node data
edit_kw = {}
quantity = len(compute_node_dict['partition_list'])
if context.getQuantity() != quantity:
  edit_kw['quantity'] = quantity

os_type = compute_node_dict.get('os_type', None)
if context.getOsType() != os_type:
  edit_kw['os_type'] = os_type

public_ipv4_address = compute_node_dict.get('public_ipv4_address', None)
if context.getPublicIpv4Address() != public_ipv4_address:
  edit_kw['public_ipv4_address'] = public_ipv4_address

slapos_version = compute_node_dict.get('slapos_version', None)
if context.getSlaposVersion() != slapos_version:
  edit_kw['slapos_version'] = slapos_version

if edit_kw:
  context.edit(**edit_kw)

compareAndUpdateAddressList(context, [{'addr': compute_node_dict['address'], 'netmask': compute_node_dict['netmask']}])
expected_partition_dict = {}
for send_partition in compute_node_dict['partition_list']:
  partition = existing_partition_dict.get(send_partition['reference'], None)
  expected_partition_dict[send_partition['reference']] = True
  if partition is None:
    partition = context.newContent(portal_type='Compute Partition')
    partition.validate()
    partition.markFree()
  elif partition.getSlapState() == 'inactive':
    # Reactivate partition
    partition.markFree(comment="Reactivated by slapformat")

  if partition.getValidationState() == "invalidated":
    partition.validate(comment="Reactivated by slapformat")
  if partition.getReference() != send_partition['reference']:
    partition.edit(reference=send_partition['reference'])

  send_capability_list = send_partition.get('capability_list') or []
  if partition.getSubjectList() != send_capability_list:
    partition.edit(subject=send_capability_list)

  network_interface = send_partition['tap']['name']
  compareAndUpdateAddressList(partition, send_partition['address_list'], {'network_interface': network_interface})
  tap_addr_list = []
  additional_dict = {'network_interface':  'route_' + network_interface}
  if 'ipv4_addr' in send_partition['tap'] and send_partition['tap']['ipv4_addr']:
    tap_addr_list.append({
            'addr': send_partition['tap']['ipv4_addr'],
            'netmask': send_partition['tap']['ipv4_netmask']
      })
    additional_dict['gateway_ip_address'] = send_partition['tap']['ipv4_gateway']
    additional_dict['network_address'] = send_partition['tap']['ipv4_network']
  compareAndUpdateAddressList(partition, tap_addr_list, additional_dict)

# Desactivate all other partitions
for key, value in existing_partition_dict.items():
  if key not in expected_partition_dict:
    if value.getSlapState() == "free":
      value.markInactive(comment="Desactivated by slapformat")
    if value.getValidationState() == "validated":
      value.invalidate(comment="Desactivated by slapformat")
