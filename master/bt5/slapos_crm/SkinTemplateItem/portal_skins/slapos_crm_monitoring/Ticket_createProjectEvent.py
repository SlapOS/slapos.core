"""Generic script to add event
It creates new Event for any context which become follow_up of created Event.
"""
from erp5.component.tool.NotificationTool import buildEmailMessage
from Products.ERP5Type.Utils import str2bytes

from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ticket = context
REQUEST = context.REQUEST

# Max ~3Mb
if int(REQUEST.getHeader('Content-Length', 0)) > 3145728:
  raise ValueError('Huge attachment is not supported')

# Compatibility with previous usage
if (content_type is not None) and (content_type != 'text/plain'):
  raise ValueError('Unsupported text content_type: %s' % content_type)

# Create a mail message to allow attachment in the event
attachment_list = []
if attachment:
  # Build dict wrapper for NotificationTool
  mime_type = attachment.headers.get('Content-Type', '')
  content = attachment.read()
  name = getattr(attachment, 'filename', None)
  attachment = dict(mime_type=mime_type,
                    content=content,
                    name=name)
  attachment_list.append(attachment)

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

if (notification_message is not None) and (attachment is not None):
  raise ValueError('Can not add attachment to a notification message')

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
  email = buildEmailMessage(from_url=None,
                            to_url=None,
                            msg=text_content,
                            subject=title,
                            attachment_list=attachment_list)
  event.edit(
    data=str2bytes(email.as_string())
  )

if not keep_draft:
  if direction == 'incoming':
    # Support event_workflow and event_simulation_workflow
    if portal.portal_workflow.isTransitionPossible(event, 'receive'):
      event.receive(comment=comment)
    if portal.portal_workflow.isTransitionPossible(event, 'stop'):
      event.stop(comment=comment)
  else:
    if portal.portal_workflow.isTransitionPossible(event, 'plan'):
      event.plan(comment=comment)
    if portal.portal_workflow.isTransitionPossible(event, 'start'):
      event.start(comment=comment, send_mail=(portal_type == 'Mail Message'))
    if portal.portal_workflow.isTransitionPossible(event, 'stop'):
      event.stop(comment=comment)
    event.deliver(comment=comment)

return event
