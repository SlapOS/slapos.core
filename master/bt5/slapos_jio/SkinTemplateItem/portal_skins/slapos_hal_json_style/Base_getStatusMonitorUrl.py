from ZTUtils import make_query
# TODO how to avoid hardcode here? from InstanceTree_getConnectionParameterList?
base_url = 'https://monitor.app.officejs.com/#/?'
url_parameter_kw = { 'page': 'ojsm_landing' }

instance_tree = context
if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  instance_tree = context.getSpecialise()
connection_parameter_dict = instance_tree.InstanceTree_getMonitorParameterDict()
if all(key in connection_parameter_dict for key in ('username', 'password', 'url')):
  url_parameter_kw['username'] = connection_parameter_dict['username']
  url_parameter_kw['password'] = connection_parameter_dict['password']
  url_parameter_kw['url'] = connection_parameter_dict['url']

if context.getPortalType() == "Instance Tree":
  for connection_parameter in context.InstanceTree_getConnectionParameterList(raw=True):
    if 'connection_key' in connection_parameter and connection_parameter['connection_key'] == "monitor-setup-url":
      return connection_parameter['connection_value']
  url_parameter_kw['query'] = 'portal_type:"Instance Tree" AND title:"%s"' % context.getTitle()

if context.getPortalType() in ["Software Instance", "Slave Instance"]:
  url_parameter_kw['query'] = 'portal_type:"Software Instance" AND title:"%s" AND ' % context.getTitle() + 'specialise_title:"%s"' % context.getSpecialiseTitle()

return base_url + make_query(url_parameter_kw)
