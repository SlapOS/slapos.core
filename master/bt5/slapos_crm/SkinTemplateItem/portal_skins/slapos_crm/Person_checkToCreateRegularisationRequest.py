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
  default_source_project_uid=person.getUid(),
  simulation_state=['suspended', 'validated'],
)

if ticket is not None:
  return ticket, None

outstanding_amount = person.Entity_statSlapOSOutstandingAmount()

# Amount to be ignored, as it comes from the first invoice generated
# after the subscription. We do not take it into account as no service
# was provided yet.
unpaid_payment_amount = 0
for payment in person.Person_getSubscriptionRequestFirstUnpaidPaymentList():
  unpaid_payment_amount += payment.PaymentTransaction_getTotalPayablePrice()

# It can't be smaller, we are considernig all open invoices are from unpaid_payment_amount
if round(float(outstanding_amount), 2) == round(-float(unpaid_payment_amount), 2):
  return ticket, None

if int(outstanding_amount) > 0:
  tag = "%s_addRegularisationRequest_inProgress" % person.getUid()
  if (portal.portal_activities.countMessageWithTag(tag) > 0):
    # The regularisation request is already under creation but can not be fetched from catalog
    # As it is not possible to fetch informations, it is better to raise an error
    return None, None

  # Prevent concurrent transaction to create 2 tickets for the same person
  person.serialize()

  # Time to create the ticket
  regularisation_request_template = portal.restrictedTraverse(
    portal.portal_preferences.getPreferredRegularisationRequestTemplate())
  ticket = regularisation_request_template.Base_createCloneDocument(batch_mode=1)
  ticket.edit(
    source_project_value=context,
    title='Account regularisation expected for "%s"' % context.getTitle(),
    destination_decision_value=context,
    destination_value=context,
    start_date=DateTime(),
    resource=portal.portal_preferences.getPreferredRegularisationRequestResource(),
  )
  ticket.validate(comment='New automatic ticket for %s' % context.getTitle())
  ticket.suspend(comment='New automatic ticket for %s' % context.getTitle())

  ticket.reindexObject(activate_kw={'tag': tag})

  # Notify using user's language
  language = context.getLanguage("en")

  notification_message = context.getPortalObject().portal_notifications.getDocumentValue(
    reference="slapos-crm.create.regularisation.request",
    language=language)
  if notification_message is None:
    subject = 'Invoice payment requested'
    body = """Dear %s,

A new invoice has been generated. 
You can access it in your invoice section at %s.

Regards,
The slapos team
""" % (context.getTitle(), portal.portal_preferences.getPreferredSlaposWebSiteUrl())

  else:
    notification_mapping_dict = {
     'user_name': context.getTitle()}

    subject = notification_message.getTitle()

    # Preserve HTML else convert to text
    if notification_message.getContentType() == "text/html":
      body = notification_message.asEntireHTML(
        substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})
    else:
      body = notification_message.asText(
        substitution_method_parameter_dict={'mapping_dict':notification_mapping_dict})

  mail_message = ticket.RegularisationRequest_checkToSendUniqEvent(
    portal.portal_preferences.getPreferredRegularisationRequestResource(),
    subject,
    body,
    'Requested manual payment.')

  return ticket, mail_message

return ticket, None
