from DateTime import DateTime
portal = context.getPortalObject()

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop ticket creation
  return

if context.getMonitorScope() == "disabled":
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

support_request = context.Base_generateSupportRequestForSlapOS(
  ticket_title,
  description,
  context.getRelativeUrl()
)

person = context.getSourceAdministrationValue(portal_type="Person")
if not person:
  return support_request

# Send Notification message
notification_reference = 'slapos-crm-compute_node_check_state.notification'
notification_message = portal.portal_notifications.getDocumentValue(
                reference=notification_reference)

if notification_message is None:
  message = """%s""" % description
else:
  mapping_dict = {'compute_node_title':context.getTitle(),
                  'compute_node_id':reference,
                  'last_contact':last_contact}
  message = notification_message.asText(
            substitution_method_parameter_dict={'mapping_dict':mapping_dict})

support_request.SupportRequest_trySendNotificationMessage(
            ticket_title,
            message, person.getRelativeUrl())
              
return support_request
