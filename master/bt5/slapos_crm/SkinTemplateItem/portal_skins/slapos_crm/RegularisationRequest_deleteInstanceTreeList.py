from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ticket = context
state = ticket.getSimulationState()
person = ticket.getDestinationDecisionValue(portal_type="Person")
if (state == 'suspended') and \
   (person is not None) and \
   (ticket.getResource() == 'service_module/slapos_crm_delete_acknowledgement'):

  portal = context.getPortalObject()
  subscribed_item_list = []

  ledger_uid = portal.portal_categories.ledger.automated.getUid()
  # Gather the list of not paid services
  for outstanding_amount in person.Entity_getOutstandingAmountList(
    ledger_uid=ledger_uid,
    include_planned=True
  ):
    for outstanding_invoice in person.Entity_getOutstandingAmountList(
      section_uid=outstanding_amount.getSourceSectionUid(),
      resource_uid=outstanding_amount.getPriceCurrencyUid(),
      ledger_uid=outstanding_amount.getLedgerUid(),
      group_by_node=False
    ):
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
          subscribed_item_list.append(subscribed_item)

      if subscribed_item is None:
        raise NotImplementedError('Unhandled invoice %s' % outstanding_invoice.getRelativeUrl())

  for subscribed_item in subscribed_item_list:
    if ((subscribed_item.getPortalType() == 'Compute Node') and
          (subscribed_item.getAllocationScope() != 'close/forever')):
      # allow cleaning up the compute node even if deleted
      subscribed_item.edit(allocation_scope='close/forever')
    elif (subscribed_item.getPortalType() == 'Instance Tree'):
      # change the slap state to deleted, to allow propagation of the state
      # even on remote node
      subscribed_item.InstanceTree_deleteFromRegularisationRequest(person.getRelativeUrl())
    elif ((subscribed_item.getPortalType() == 'Project') and
          (subscribed_item.getValidationState() != 'invalidated')):
      # do not close the project until all node and instance trees are corrected deleted
      can_invalidate_project = True
      for other_item in  portal.portal_catalog(
        portal_type=['Compute Node', 'Instance Tree'],
        follow_up__uid=subscribed_item.getUid()
      ):
        if other_item.getValidationState() not in ['invalidated', 'archived']:
          can_invalidate_project = False
          subscribed_item_list.append(other_item)
      if can_invalidate_project:
        subscribed_item.invalidate(comment='Not paid')

  return True
return False
