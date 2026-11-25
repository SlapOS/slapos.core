from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
entity = context
ticket_portal_type = "Regularisation Request"
actor_currency_seen_dict = {}
result_list = []

for outstanding_invoice in entity.Entity_getOutstandingInvoiceList():
  actor = outstanding_invoice.getDestinationValue()
  currency = outstanding_invoice.getPriceCurrencyValue()

  seen_key = '%s___%s' % (actor.getRelativeUrl(), currency.getRelativeUrl())
  if seen_key in actor_currency_seen_dict:
    continue
  else:
    actor_currency_seen_dict[seen_key] = True

  # XXX TODO
  # # Prevent to create 2 tickets during the same transaction
  # transactional_variable = getTransactionalVariable()
  # if tag in transactional_variable:
  #   raise RuntimeError, 'ticket %s already exist' % tag
  # else:
  #   transactional_variable[tag] = None

  ticket = portal.portal_catalog.getResultValue(
    portal_type=ticket_portal_type,
    destination__uid=actor.getUid(),
    destination_section__uid=entity.getUid(),
    price_currency__uid=currency.getUid(),
    simulation_state=['suspended', 'validated'],
  )

  if ticket is not None:
    result_list.append((ticket, None))
    continue

  message = None
  tag = "%s_%s_%s_addRegularisationRequest_inProgress" % (actor.getUid(), entity.getUid(), currency.getUid())
  if (portal.portal_activities.countMessageWithTag(tag) > 0):
    # The regularisation request is already under creation but can not be fetched from catalog
    # As it is not possible to fetch informations, it is better to raise an error
    result_list.append((None, None))
    continue

  # Prevent concurrent transaction to create 2 tickets for the same person
  entity.serialize()

  # Time to create the ticket
  comment = 'New automatic ticket for %s' % entity.getTitle()
  ticket = entity.Entity_createTicketFromTradeCondition(
    portal.service_module.slapos_crm_acknowledgement.getRelativeUrl(),
    'Account regularisation expected for "%s"' % entity.getTitle(),
    '',
    portal_type='Regularisation Request',
    comment=comment,
    destination_decision=actor.getRelativeUrl(),
    price_currency=currency.getRelativeUrl(),
  )

  subject = 'Invoice payment requested'
  body = """Dear %s,

A new invoice has been generated.

Regards,
Administrator
""" % (actor.getTitle())

  message = ticket.RegularisationRequest_checkToSendUniqEvent(
    ticket.getResource(), subject, body, 'Requested manual payment.',
    notification_message="slapos-crm.create.regularisation.request",
    substitution_method_parameter_dict={
      'user_name': actor.getTitle()
    },
  )
  ticket.validate(comment=comment)
  ticket.reindexObject(activate_kw={'tag': tag})
  result_list.append((ticket, message))

return result_list
