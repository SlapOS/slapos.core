monitor_url = context.Base_getMonitorBaseUrl()
base_url = monitor_url + '#/?page=ojsm_dispatch&query=portal_type:"Software Instance" AND '

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  base_url = monitor_url + '#/?page=ojsm_dispatch&query=portal_type:"Instance Tree" AND '
  return base_url + "title:(%s)" % context.getTitle()

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  return base_url + "reference:%s" % context.getReference()
