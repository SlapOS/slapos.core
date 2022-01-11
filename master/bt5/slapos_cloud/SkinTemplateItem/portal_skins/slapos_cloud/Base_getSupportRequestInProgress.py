portal = context.getPortalObject()

return portal.portal_catalog.getResultValue(
  portal_type='Support Request',
  title={'query': title, 'key': 'ExactMatch'},
  simulation_state=["validated", "submitted", "suspended"],
  causality__uid=context.getUid(),
)
