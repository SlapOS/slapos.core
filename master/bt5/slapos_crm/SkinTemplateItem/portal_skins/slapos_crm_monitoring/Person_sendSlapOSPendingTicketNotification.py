portal = context.getPortalObject()
start_date = DateTime()

# Rely on Trade condition (like in ticket to set the proper sender)
trade_condition = portal.sale_trade_condition_module.slapos_ticket_trade_condition

event_kw = {
  'portal_type' : "Mail Message",
  'title' : response_event_title,
  'resource' : "service_module/slapos_crm_information",
  'source' : trade_condition.getSource(),
  'destination' : context.getRelativeUrl(),
  'start_date' : start_date,
  'text_content' : response_event_text_content,
  'content_type' : 'text/plain',
  }

# Create event
event = portal.event_module.newContent(**event_kw)
event.plan()
event.start(send_mail=True, comment="Sent via Person_sendSlapOSPendingTicketNotification")

if batch_mode:
  return event

message = portal.Base_translateString('New event created.')
return event.Base_redirect(keep_items={'portal_status_message': message})
