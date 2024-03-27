from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ticket = context
service = portal.restrictedTraverse(service_relative_url)
assert service.getPortalType() == "Service"
event_portal_type = "Mail Message"

# XXX TODO
# # Prevent to create 2 tickets during the same transaction
# transactional_variable = getTransactionalVariable()
# if tag in transactional_variable:
#   raise RuntimeError, 'ticket %s already exist' % tag
# else:
#   transactional_variable[tag] = None

event = portal.portal_catalog.getResultValue(
  portal_type=event_portal_type,
  resource__uid=service.getUid(),
  follow_up__uid=ticket.getUid(),
)

if (event is None) and (ticket.getSimulationState() == 'suspended'):
  tag = "%s_addUniqEvent_%s" % (ticket.getUid(), service.getUid())
  if (portal.portal_activities.countMessageWithTag(tag) > 0):
    # The event is already under creation but can not be fetched from catalog
    return None

  # Prevent concurrent transaction to create 2 events for the same ticket
  ticket.edit(resource=service_relative_url)

  event = ticket.Ticket_createProjectEvent(
    title, 'outgoing', 'Mail Message',
    service_relative_url,
    text_content=text_content,
    content_type='text/plain',
    notification_message=notification_message,
    substitution_method_parameter_dict=substitution_method_parameter_dict,
    comment=comment
  )
  event.reindexObject(activate_kw={'tag': tag})

return event
