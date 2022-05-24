from Products.ERP5Type.UnrestrictedMethod import UnrestrictedMethod
from AccessControl.SecurityManagement import getSecurityManager, \
    setSecurityManager, newSecurityManager

@UnrestrictedMethod
def getComputeNodeReferenceAndUserId(item):
  portal_type = item.getPortalType()
  compute_node = None

  if portal_type == 'Software Installation':
    compute_node = item.getAggregateValue(portal_type='Compute Node')
  elif portal_type == 'Compute Partition':
    compute_node = item.getParentValue()
  elif portal_type in ['Software Instance', 'Slave Instance']:
    partition = item.getAggregateValue(portal_type='Compute Partition')
    if partition is not None:
      compute_node = partition.getParentValue()

  if (compute_node is not None) and \
    (compute_node.getPortalType() == 'Compute Node') and \
    (compute_node.getValidationState() == 'validated'):
    return compute_node, compute_node.getReference(), compute_node.getUserId()
  return None, None, None


def Item_activateFillComputeNodeInformationCache(state_change):
  item = state_change['object']
  portal = item.getPortalObject()
  compute_node, compute_node_reference, user_id = getComputeNodeReferenceAndUserId(item)
  if compute_node is None:
    return None

  if user_id is None:
    return None

  user = portal.acl_users.getUserById(user_id)
  if user is None:
    raise ValueError("User %s not found" % user_id)

  sm = getSecurityManager()
  try:
    newSecurityManager(None, user)
    compute_node._activateFillComputeNodeInformationCache(
      compute_node_reference)
  finally:
    setSecurityManager(sm)


@UnrestrictedMethod
def reindexPartition(item):
  partition = item.getAggregateValue(portal_type='Compute Partition')
  if partition is not None:
    partition.reindexObject()


def Instance_reindexComputePartition(state_change):
  item = state_change['object']
  reindexPartition(item)
