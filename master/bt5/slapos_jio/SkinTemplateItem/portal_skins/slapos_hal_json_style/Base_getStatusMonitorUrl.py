monitor_dict = context.Base_getMonitorDict()
base_url = monitor_dict["url"]

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  connection_parameter_dict = context.InstanceTree_getMonitorParameterDict()
  connection_url = '&url=%s'% connection_parameter_dict['url'] + '&username=%s'% connection_parameter_dict['username'] + '&password=%s'% connection_parameter_dict['password']
  return base_url + '&query=portal_type:"Instance Tree" AND title:(%s)' % context.getTitle() + connection_url

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  it = context.getSpecialise()
  connection_parameter_dict = it.InstanceTree_getMonitorParameterDict()
  connection_url = '&url=%s'% connection_parameter_dict['url'] + '&username=%s'% connection_parameter_dict['username'] + '&password=%s'% connection_parameter_dict['password']
  return base_url + '&query=portal_type:"Software Instance" AND title:"%s" AND ' % context.getTitle() + 'specialise_title:"%s"' % context.getSpecialiseTitle() + connection_url

#OLD return query_url + "reference:%s" % context.getReference()
