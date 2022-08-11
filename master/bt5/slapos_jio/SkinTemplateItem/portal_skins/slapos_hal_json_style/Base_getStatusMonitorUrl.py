base_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type:"Software Instance" AND '

if context.getPortalType() == "Organisation":
  compute_node_reference = ",".join([ '"' + i.getReference() + '"' for i in context.Organisation_getComputeNodeTrackingList()])
  return base_url + "aggregate_reference:(%s)" % compute_node_reference

if context.getPortalType() == "Project":
  compute_node_reference = ",".join([ '"' + i.getReference() + '"' for i in context.Project_getComputeNodeTrackingList()])
  return base_url + "aggregate_reference:(%s)" % compute_node_reference

if context.getPortalType() == "Computer Network":
  compute_node_reference = ",".join([ '"' + i.getReference() + '"' for i in context.getSubordinationRelatedValueList(portal_type="Compute Node")])
  return base_url + "aggregate_reference:(%s)" % compute_node_reference

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  base_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type:"Instance Tree" AND '
  return base_url + "title:(%s)" % context.getTitle()

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  return base_url + "reference:%s" % context.getReference()

if context.getPortalType() == "Compute Node":
  return base_url + "aggregate_reference:%s" % context.getReference()
