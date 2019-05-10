portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop verification if there are too much tickets
  return

portal.portal_catalog.searchAndActivate(
    portal_type='Hosting Subscription',
    validation_state='validated',
    method_id='HostingSubscription_checkSoftwareInstanceState',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
