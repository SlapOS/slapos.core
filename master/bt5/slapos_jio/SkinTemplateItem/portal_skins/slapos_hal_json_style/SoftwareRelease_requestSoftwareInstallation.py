import json
portal = context.getPortalObject()

compute_node = portal.restrictedTraverse(compute_node)

compute_node.requestSoftwareRelease(
  software_release_url=context.getUrlString(),
  state='available')

return json.dumps(context.REQUEST.get('software_installation_url'))
