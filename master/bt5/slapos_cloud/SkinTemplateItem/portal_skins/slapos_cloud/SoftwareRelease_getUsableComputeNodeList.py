kw['portal_type'] = 'Software Installation'
kw['validation_state'] = 'validated'
kw['url_string'] = context.getUrlString()

software_installation_list = context.portal_catalog(**kw)
compute_node_list = []
allocation_scope_list = ['open/personal', 'open/public', 'open/friend']
for software_installation in software_installation_list:
  compute_node = software_installation.getAggregateValue()
  if software_installation.getSlapState() == 'start_requested' and \
              compute_node.getAllocationScope() in allocation_scope_list:
    compute_node_list.append(compute_node)

return compute_node_list
