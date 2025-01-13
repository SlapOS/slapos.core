from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
person = context
ticket_portal_type = "Regularisation Request"

# XXX TODO
# # Prevent to create 2 tickets during the same transaction
# transactional_variable = getTransactionalVariable()
# if tag in transactional_variable:
#   raise RuntimeError, 'ticket %s already exist' % tag
# else:
#   transactional_variable[tag] = None

ticket = portal.portal_catalog.getResultValue(
  portal_type=ticket_portal_type,
  destination__uid=person.getUid(),
  simulation_state=['suspended', 'validated'],
)

if ticket is not None:
  return ticket, None

mail_message = None
if person.Entity_hasOutstandingAmount(ledger_uid=portal.portal_categories.ledger.automated.getUid()):
  tag = "%s_addRegularisationRequest_inProgress" % person.getUid()
  if (portal.portal_activities.countMessageWithTag(tag) > 0):
    # The regularisation request is already under creation but can not be fetched from catalog
    # As it is not possible to fetch informations, it is better to raise an error
    return None, None

  # Prevent concurrent transaction to create 2 tickets for the same person
  person.serialize()

  # Time to create the ticket
  comment = 'New automatic ticket for %s' % context.getTitle()
  ticket = context.Entity_createTicketFromTradeCondition(
    portal.service_module.slapos_crm_acknowledgement.getRelativeUrl(),
    'Account regularisation expected for "%s"' % context.getTitle(),
    '',
    portal_type='Regularisation Request',
    comment=comment
  )
  ticket.validate(comment=comment)
  ticket.suspend(comment=comment)

  ticket.reindexObject(activate_kw={'tag': tag})

  subject = 'Invoice payment requested'
  body = """Dear %s,

A new invoice has been generated.
You can access it in your invoice section at %s.

Regards,
The slapos team
""" % (context.getTitle(), portal.portal_preferences.getPreferredSlaposWebSiteUrl())
  notification_message_reference = "slapos-crm.create.regularisation.request"

  mail_message = ticket.RegularisationRequest_checkToSendUniqEvent(
    portal.portal_preferences.getPreferredRegularisationRequestResource(),
    subject,
    body,
    'Requested manual payment.',
    notification_message=notification_message_reference,
    substitution_method_parameter_dict={
      'user_name': context.getTitle()
    },
  )

return ticket, mail_message
