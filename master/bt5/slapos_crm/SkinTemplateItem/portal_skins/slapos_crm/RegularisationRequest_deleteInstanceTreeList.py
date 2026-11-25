from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
ticket = context
state = ticket.getSimulationState()
entity = ticket.getDestinationSectionValue(portal_type=portal.getPortalEntityTypeList())
actor_relative_url = ticket.getDestination(portal_type=portal.getPortalActorTypeList())
if (state == 'suspended') and \
   (entity is not None) and \
   (ticket.getResource() == 'service_module/slapos_crm_delete_acknowledgement'):

  subscribed_item_list = []

  for outstanding_invoice in entity.Entity_getOutstandingInvoiceList():
    if outstanding_invoice.getDestination() == actor_relative_url:
      subscribed_item = None
      for invoice_line in outstanding_invoice.getMovementList(
        portal_type=['Invoice Line', 'Invoice Cell']
      ):
        hosting_subscription = invoice_line.getAggregateValue(portal_type='Hosting Subscription')
        if hosting_subscription is not None:
          subscribed_item = invoice_line.getAggregateValue(portal_type=[
            'Instance Tree',
            'Project'
          ])
          if subscribed_item is not None:
            subscribed_item_list.append(subscribed_item)

  for subscribed_item in subscribed_item_list:
    if ((subscribed_item.getPortalType() == 'Compute Node') and
          (subscribed_item.getAllocationScope() != 'close/forever')):
      # allow cleaning up the compute node even if deleted
      subscribed_item.edit(allocation_scope='close/forever')
    elif (subscribed_item.getPortalType() == 'Instance Tree'):
      # change the slap state to deleted, to allow propagation of the state
      # even on remote node
      subscribed_item.InstanceTree_deleteFromRegularisationRequest(actor_relative_url)
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
          subscribed_item_list.append(other_item) # pylint: disable=modified-iterating-list
      if can_invalidate_project:
        subscribed_item.invalidate(comment='Not paid')

  return True
return False
