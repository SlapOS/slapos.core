# TODO how to avoid hardcode here? from InstanceTree_getConnectionParameterList?
base_url = 'https://monitor.app.officejs.com/#/?page=ojsm_landing'

try:
  instance_tree = context
  if context.getPortalType() in ["Software Instance", "Slave Instance"]:
    instance_tree = context.getSpecialise()
  connection_parameter_dict = instance_tree.InstanceTree_getMonitorParameterDict()
  connection_url = '&url=%s'% connection_parameter_dict['url'] + '&username=%s'% connection_parameter_dict['username'] + '&password=%s'% connection_parameter_dict['password']
except (AttributeError, TypeError) as _:
  connection_url = ''

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if connection_parameter['connection_key'] == "monitor-setup-url":
      # connection_parameter['connection_value'] looks like #page=settings_configurator&url=xx/public/feeds&username=admin&password=yy
      # workaround until settings_configurator is c on software releases / buildout cfg files are updated
      return connection_parameter['connection_value'].replace("settings_configurator", "ojsm_landing")
  return base_url + '&query=portal_type:Instance Tree AND title:%s' % context.getTitle() + connection_url

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  return base_url + '&query=portal_type:Software Instance AND title:%s AND ' % context.getTitle() + 'specialise_title:%s' % context.getSpecialiseTitle() + connection_url
