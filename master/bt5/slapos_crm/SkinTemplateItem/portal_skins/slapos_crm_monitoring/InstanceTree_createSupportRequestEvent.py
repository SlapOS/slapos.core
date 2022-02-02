portal = context.getPortalObject()

ticket_title = "Instance Tree %s is failing." % context.getTitle()
error_message = instance.SoftwareInstance_hasReportedError(include_message=True)

description = "%s contains software instances which are unallocated or reporting errors." % (
        context.getTitle())
if error_message:
  description += "\n\nMessage: %s" % error_message
else:
  error_message = "No message!"

support_request = context.Base_generateSupportRequestForSlapOS(
  ticket_title,
  description,
  context.getRelativeUrl())

if support_request is None:
  return

person = context.getDestinationSectionValue(portal_type="Person")
if not person:
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

support_request.notify(message_title="Instance Tree was destroyed was destroyed by the user",
              message=message,
              destination_relative_url=person.getRelativeUrl())

return context.REQUEST.get("ticket_notified_item")
