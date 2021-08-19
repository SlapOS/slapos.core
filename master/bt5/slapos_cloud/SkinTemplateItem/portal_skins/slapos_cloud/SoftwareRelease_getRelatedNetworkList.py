network_list = []
for compute_node in context.SoftwareRelease_getUsableComputeNodeList():
  network = compute_node.getSubordinationValue()
  if network and not network in network_list:
    network_list.append(network)

return network_list
