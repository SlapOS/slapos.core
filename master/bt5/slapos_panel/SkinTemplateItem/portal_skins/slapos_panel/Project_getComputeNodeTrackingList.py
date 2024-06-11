kw.update({
  "follow_up__uid": context.getUid(),
  "portal_type": ['Instance Node', 'Remote Node', 'Compute Node', 'Instance Tree', 'Computer Network'],
  "validation_state": "validated"
})

return context.getPortalObject().portal_catalog(**kw)
