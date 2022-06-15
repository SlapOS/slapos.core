"""Generic script to add event
It creates new Event for any context which become follow_up of created Event.
"""
portal = context.getPortalObject()
ticket = context

if direction == 'outgoing':
  source_relative_url = source or ticket.getSource()
  source_section_relative_url = ticket.getSourceSection()
  source_project_relative_url = ticket.getSourceProject()
  destination_relative_url = destination or ticket.getDestination()
  destination_section_relative_url = ticket.getDestinationSection()
  destination_project_relative_url = ticket.getDestinationProject()
elif direction == 'incoming':
  source_relative_url = source or ticket.getDestination()
  source_section_relative_url = ticket.getDestinationSection()
  source_project_relative_url = ticket.getDestinationProject()
  destination_relative_url = destination or ticket.getSource()
  destination_section_relative_url = ticket.getSourceSection()
  destination_project_relative_url = ticket.getSourceProject()
else:
  raise NotImplementedError('The specified direction is not handled: %r' % (direction,))

event_kw = {
  'portal_type': portal_type,
  'resource': resource,
  'source': source_relative_url,
  'source_section': source_section_relative_url,
  'source_project': source_project_relative_url,
  'destination': destination_relative_url,
  'destination_section': destination_section_relative_url,
  'destination_project': destination_project_relative_url,
  'start_date': DateTime(),
  'follow_up_value': ticket,
  'language': language,
  'text_content': text_content,
  'content_type': content_type,
  }
# Create event
module = portal.getDefaultModule(portal_type=portal_type)
event = module.newContent(**event_kw)

if notification_message:
  event.Event_setTextContentFromNotificationMessage(
    notification_message,
    language=language,
    substitution_method_parameter_dict=substitution_method_parameter_dict
  )

# Prefer using the notification message title
# as it will be correctly translated
if not event.hasTitle():
  event.edit(title=title)

if not keep_draft:
  if direction == 'incoming':
    # Support event_workflow and event_simulation_workflow
    if portal.portal_workflow.isTransitionPossible(event, 'receive'):
      event.receive(comment=comment)
    if portal.portal_workflow.isTransitionPossible(event, 'stop'):
      event.stop(comment=comment)
  else:
    event.plan(comment=comment)
    event.start(comment=comment, send_mail=(portal_type == 'Mail Message'))
    event.stop(comment=comment)
    event.deliver(comment=comment)

return event
