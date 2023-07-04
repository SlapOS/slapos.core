from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

node_dict = {}
for compute_node in compute_node_list:
  node_dict[compute_node.getReference()] = compute_node.getAccessStatus()

return {"compute_node": node_dict,
        "reference": context.getReference(),
        "portal_type": context.getPortalType()}
