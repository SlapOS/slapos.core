base_url = 'https://monitor.app.officejs.com/#/?page=ojsm_dispatch&query=portal_type:"Software Instance" AND '

if context.getPortalType() == "Organisation":
  compute_node_reference = ",".join([ '"' + i.getReference() + '"' for i in context.Organisation_getComputeNodeTrackingList()])
  return context.REQUEST.RESPONSE.redirect(base_url + "aggregate_reference:(%s)" % compute_node_reference)

if context.getPortalType() == "Project":
  compute_node_reference = ",".join([ '"' + i.getReference() + '"' for i in context.Project_getComputeNodeTrackingList()])
  return context.REQUEST.RESPONSE.redirect(base_url + "aggregate_reference:(%s)" % compute_node_reference)
