monitor_dict = context.Base_getMonitorDict()
base_url = monitor_dict["url"] + '#/?page=' + monitor_dict["dispatch_page"]

query_url = base_url + '&query=portal_type:"Software Instance" AND '

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  query_url = base_url + '&query=portal_type:"Instance Tree" AND '
  return query_url + "title:(%s)" % context.getTitle()

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  return query_url + 'title:"%s" AND ' % context.getTitle() + 'specialise_title:"%s"' % context.getSpecialiseTitle()
