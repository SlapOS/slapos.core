portal = context.getPortalObject()


person = context.getDestinationSectionValue()
if person is None or portal.ERP5Site_isSupportRequestCreationClosed(person.getRelativeUrl()):
  # Stop ticket creation
  return

ticket_title = "Instance Tree %s is failing." % context.getTitle()
error_message = instance.SoftwareInstance_hasReportedError(include_message=True)

description = "%s contains software instances which are unallocated or reporting errors." % (
        context.getTitle())
if error_message:
  description += "\n\nMessage: %s" % error_message
else:
  error_message = "No message!"

support_request = person.Base_getSupportRequestInProgress(
    title=ticket_title,
    aggregate=context.getRelativeUrl())

if support_request is None:
  person.notify(support_request_title=ticket_title,
              support_request_description=description,
              aggregate=context.getRelativeUrl())

  support_request_relative_url = context.REQUEST.get("support_request_relative_url")
  if support_request_relative_url is None:
    return

  support_request = portal.restrictedTraverse(support_request_relative_url)

if support_request is None:
  return

if support_request.getSimulationState() not in ["validated", "suspended"]:
  support_request.validate()

# Send Notification message
message = description
notification_message = portal.portal_notifications.getDocumentValue(
                 reference=notification_message_reference)
if notification_message is not None:
  mapping_dict = {'instance_tree_title':context.getTitle(),
                  'instance': instance.getTitle(),
                  'error_text': error_message}

  message = notification_message.asText(
              substitution_method_parameter_dict={'mapping_dict':mapping_dict})

event = support_request.SupportRequest_getLastEvent(ticket_title)
if event is None:
  support_request.notify(message_title=ticket_title, message=message)

return context.REQUEST.get("ticket_notified_item")
