portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
    portal_type='Instance Tree',
    validation_state='validated',
    method_id='InstanceTree_checkSoftwareInstanceState',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
