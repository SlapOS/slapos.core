portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop verification if there are too much tickets
  return

portal.portal_catalog.searchAndActivate(
    portal_type='Instance Tree',
    validation_state='validated',
    method_id='InstanceTree_checkSoftwareInstanceState',
    # This alarm bruteforce checking all documents,
    # without changing them directly.
    # Increase priority to not block other activities
    activate_kw = {'tag':tag, 'priority': 2}
  )

context.activate(after_tag=tag).getId()
