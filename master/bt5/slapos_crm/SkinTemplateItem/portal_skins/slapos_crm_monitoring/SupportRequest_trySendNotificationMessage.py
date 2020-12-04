support_request = context
portal = context.getPortalObject()

resource = portal.service_module.slapos_crm_information.getRelativeUrl()
# create Web message if needed for this ticket
last_event = context.portal_catalog.getResultValue(
             title=message_title,
             follow_up_uid=support_request.getUid(),
             sort_on=[('delivery.start_date', 'DESC')],
)
if last_event:
  # User has already been notified for this problem.
  return last_event

transactional_event = context.REQUEST.get("support_request_notified_item", None)

if transactional_event is not None:
  if (transactional_event.getFollowUpUid() == support_request.getUid()) and \
    (transactional_event.getTitle() == message_title):
    return transactional_event

template = portal.restrictedTraverse(
        portal.portal_preferences.getPreferredWebMessageTemplate())

event = template.Base_createCloneDocument(batch_mode=1)
event.edit(
  title=message_title,
  text_content=message,
  start_date = DateTime(),
  resource = resource,
  source=support_request.getSource(),
  destination=destination_relative_url,
  follow_up=support_request.getRelativeUrl(),
)
event.stop()
event.deliver()

support_request.serialize()
context.REQUEST.set("support_request_notified_item", event)

return event
