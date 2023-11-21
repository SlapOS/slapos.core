from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

compute_node = context.getObject()
computer_network = compute_node.getSubordinationValue()

if (computer_network is not None) and (compute_node.getFollowUp() != computer_network.getFollowUp()):
  compute_node.edit(subordination=None)
