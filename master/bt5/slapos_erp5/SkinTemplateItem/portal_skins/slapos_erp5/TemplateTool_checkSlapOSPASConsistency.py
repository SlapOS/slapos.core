import six
portal = context.getPortalObject()
slapos_plugin_dict = {
  'IExtractionPlugin': [
    'ERP5 Dumb HTTP Extraction Plugin',
    'ERP5 External Authentication Plugin',
    'ERP5 Access Token Extraction Plugin',
    'ERP5 Google Extraction Plugin',
    'ERP5 Facebook Extraction Plugin'
  ],
  'IGroupsPlugin': [
    'ZODB Group Manager',
    'SlapOS Shadow Authentication Plugin',
    'ERP5 Group Manager'
  ],
  'IUserEnumerationPlugin': [
    'ZODB User Manager',
    'SlapOS Shadow Authentication Plugin',
    'ERP5 Login User Manager'
  ]
}

def mergePASDictDifference(portal, d, fixit):
  plugins = portal.acl_users.plugins
  plugin_type_info = plugins.listPluginTypeInfo()
  error_list = []
  for plugin, active_list in six.iteritems(d):
    plugin_info = [q for q in plugin_type_info if q['id'] == plugin][0]
    found_list = plugins.listPlugins(plugin_info['interface'])
    meta_type_list = [q[1].meta_type for q in found_list]
    for expected in active_list:
      if expected not in meta_type_list:
        error = 'Plugin %s missing %s.' % (plugin, expected)
        if fixit:
          existing = [q for q in portal.acl_users.objectValues() if q.meta_type == expected]
          if len(existing) == 0:
            error_list.append('%s not found' % expected)
          else:
            plugins.activatePlugin(plugin_info['interface'], existing[0].getId())
            error += ' Fixed.'
        error_list.append(error)

    for activated_plugin in meta_type_list:
      if activated_plugin not in active_list:
        error = 'Plugin %s must not be activated %s.' % (plugin, activated_plugin)
        if fixit:
          existing = [q for q in portal.acl_users.objectValues() if q.meta_type == activated_plugin]
          if len(existing) == 0:
            error_list.append('%s not found' % activated_plugin)
          else:
            plugins.deactivatePlugin(plugin_info['interface'], existing[0].getId())
            error += ' Fixed.'
        error_list.append(error)

  return error_list

pas_difference = mergePASDictDifference(portal, slapos_plugin_dict, fixit)
if len(pas_difference) != 0:

  message = "PAS not configured as expected"
  if fixit:
    message += ' (fixed). '
  else:
    message += ". "
  message += "Difference:\n%s" % ('\n'.join(pas_difference), )
  return [message]

return []
