monitor_dict = context.Base_getMonitorDict()
base_url = monitor_dict["url"] + monitor_dict["dispatch_parameters"]

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  return base_url + '&query=portal_type:"Instance Tree" AND title:(%s)' % context.getTitle()

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  return base_url + '&query=portal_type:"Software Instance" AND title:"%s" AND ' % context.getTitle() + 'specialise_title:"%s"' % context.getSpecialiseTitle()
