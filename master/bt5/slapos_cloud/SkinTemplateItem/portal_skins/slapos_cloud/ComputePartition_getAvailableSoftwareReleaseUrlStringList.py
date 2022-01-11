slap_state = context.getSlapState()
portal = context.getPortalObject()

compute_node = context.getParentValue()

if slap_state == 'free':
  # XXX Not very elegant
  if (compute_node.getPortalType() == 'Remote Node'):
    return ['ANY_URL']
  return compute_node.ComputeNode_getSoftwareReleaseUrlStringList()

elif slap_state == 'busy':

  instance = portal.portal_catalog.getResultValue(
    portal_type="Software Instance",
    aggregate__uid=context.getUid(),
  )
  if (instance is None):
    # XXX Not very elegant
    if (compute_node.getPortalType() == 'Remote Node') and (context.getId() == 'SHARED_REMOTE'):
      return ['ANY_URL']
    return ['INSTANCE NOT INDEXED YET']
  else:
    return [instance.getUrlString()]

else:
  return []
