from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ticket = context
state = ticket.getSimulationState()
entity = ticket.getDestinationDecisionValue(portal_type=["Person", "Organisation"])
if (state == 'suspended') and \
   (entity is not None) and \
   (ticket.getResource() in ['service_module/slapos_crm_stop_acknowledgement', 'service_module/slapos_crm_delete_reminder', 'service_module/slapos_crm_delete_acknowledgement']):

  portal = context.getPortalObject()

  ledger_uid = portal.portal_categories.ledger.automated.getUid()
  # Gather the list of not paid services
  for outstanding_amount in entity.Entity_getOutstandingAmountList(
    ledger_uid=ledger_uid,
    include_planned=True
  ):
    for outstanding_invoice in entity.Entity_getOutstandingAmountList(
      section_uid=outstanding_amount.getSourceSectionUid(),
      resource_uid=outstanding_amount.getPriceCurrencyUid(),
      ledger_uid=outstanding_amount.getLedgerUid(),
      group_by_node=False
    ):
      person = outstanding_invoice.getDestinationValue(portal_type="Person")
      subscribed_item = None
      for invoice_line in outstanding_invoice.getMovementList(
        portal_type=['Invoice Line', 'Invoice Cell']
      ):
        hosting_subscription = invoice_line.getAggregateValue(portal_type='Hosting Subscription')
        if hosting_subscription is not None:
          subscribed_item = invoice_line.getAggregateValue(portal_type=[
            'Project',
            'Instance Tree',
            'Compute Node'
          ])
          if subscribed_item is None:
            raise NotImplementedError('Unhandled invoice line %s' % invoice_line.getRelativeUrl())

          if (subscribed_item.getPortalType() == 'Instance Tree'):
            # change the slap state to stopped, to allow propagation of the state
            # even on remote node
            subscribed_item.InstanceTree_stopFromRegularisationRequest(person.getRelativeUrl())

      if subscribed_item is None:
        raise NotImplementedError('Unhandled invoice %s' % outstanding_invoice.getRelativeUrl())

  return True
return False
