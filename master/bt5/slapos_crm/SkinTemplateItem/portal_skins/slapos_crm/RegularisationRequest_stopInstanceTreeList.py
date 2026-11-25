from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

ticket = context
portal = context.getPortalObject()
state = ticket.getSimulationState()
entity = ticket.getDestinationSectionValue(portal_type=portal.getPortalEntityTypeList())
actor_relative_url = ticket.getDestination(portal_type=portal.getPortalActorTypeList())
if (state == 'suspended') and \
   (entity is not None) and \
   (ticket.getResource() in ['service_module/slapos_crm_stop_acknowledgement',
                             'service_module/slapos_crm_delete_reminder',
                             'service_module/slapos_crm_delete_acknowledgement']):

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
          ])
          if subscribed_item is None:
            # Do not touch other items
            # Idea: monitoring from project node could be disabled
            continue

          if (subscribed_item.getPortalType() == 'Instance Tree'):
            # change the slap state to stopped, to allow propagation of the state
            # even on remote node
            subscribed_item.InstanceTree_stopFromRegularisationRequest(actor_relative_url)

  return True
return False
