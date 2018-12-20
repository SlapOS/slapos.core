portal = context.getPortalObject()
portal.portal_catalog.searchAndActivate(
  portal_type='Hosting Subscription',
  validation_state = 'validated',
  slap_state=['start_requested', 'stop_requested'],
  method_id = 'HostingSubscription_createUpgradeDecision',
  packet_size=1,
  activate_kw = {'tag':tag}
)

context.activate(after_tag=tag).getId()
