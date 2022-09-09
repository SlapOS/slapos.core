portal = context.getPortalObject()

portal.portal_catalog.searchAndActivate(
    portal_type = 'Person',
    method_id = 'Person_sendPendingTicketReminder',
    activate_kw = {'tag':tag}
  )

context.activate(after_tag=tag).getId()
