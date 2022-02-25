from DateTime import DateTime
portal = context.getPortalObject()

person = context.getSourceAdministrationValue(portal_type="Person")
if not person or \
   context.getMonitorScope() == "disabled" or \
   portal.ERP5Site_isSupportRequestCreationClosed():
  return 

if context.getAllocationScope("open").startswith("close"):
  context.setMonitorScope("disabled")
  return

reference = context.getReference()
compute_node_title = context.getTitle()
ticket_title = "[MONITORING] Lost contact with compute_node %s" % reference
description = ""
last_contact = "No Contact Information"

d = context.getAccessStatus()
# Ignore if data isn't present.
if d.get("no_data") == 1:
  description = "The Compute Node %s (%s)  has not contacted the server (No Contact Information)" % (
                  compute_node_title, reference)
else:
  last_contact = DateTime(d.get('created_at'))
  if (DateTime() - last_contact) > 0.01:
    description = "The Compute Node %s (%s) has not contacted the server for more than 30 minutes" \
    "(last contact date: %s)" % (compute_node_title, reference, last_contact)
  else:
    # Nothing to notify.
    return  

person.notify(support_request_title=ticket_title,
              support_request_description=description,
              aggregate=context.getRelativeUrl())

support_request_relative_url = context.REQUEST.get("support_request_relative_url")
if support_request_relative_url is None:
  return

support_request = portal.restrictedTraverse(support_request_relative_url)

# Send Notification message
notification_message = portal.portal_notifications.getDocumentValue(
  reference='slapos-crm-compute_node_check_state.notification')

if notification_message is None:
  message = """%s""" % description
else:
  mapping_dict = {'compute_node_title':context.getTitle(),
                  'compute_node_id':reference,
                  'last_contact':last_contact}
  message = notification_message.asText(
            substitution_method_parameter_dict={'mapping_dict': mapping_dict})

support_request.notify(message_title=ticket_title,
              message=message,
              destination_relative_url=person.getRelativeUrl())

return support_request
