subscription_request = context
portal = context.getPortalObject()

def markHistory(document, comment):
  portal_workflow = document.portal_workflow
  last_workflow_item = portal_workflow.getInfoFor(ob=document,
                                          name='comment', wf_id='edit_workflow')
  if last_workflow_item != comment:
    subscription_request.Ticket_createProjectEvent(
      "Can not activate your new service: %s" % subscription_request.getAggregateTitle(),
      'outgoing', 'Web Message',
      portal.service_module.slapos_crm_information.getRelativeUrl(),
      text_content=comment,
      content_type='text/plain'
    )
    portal_workflow.doActionFor(document, action='edit_action', comment=comment)

item = subscription_request.getAggregateValue()
if item is None:
  resource = subscription_request.getResourceValue()
  raise ValueError('Unsupported resource: %s' % resource.getRelativeUrl())

  # Use list setter, to ensure it crashes if item is still None
  # subscription_request.setAggregateValueList([item])


# If the virtual master is not in the expected subscription status,
# do not accept any new service (compute node, instance) for it
if (((subscription_request.getSourceProjectValue() is not None) and
     (subscription_request.getSourceProjectValue().Item_getSubscriptionStatus() != 'subscribed')) or
    ((subscription_request.getDestinationProjectValue() is not None) and
     (subscription_request.getDestinationProjectValue().Item_getSubscriptionStatus() != 'subscribed'))):
  return markHistory(subscription_request,
                     'Virtual master subscription is not valid.')

# Accept the subscription only if user paid the security payment
total_price = subscription_request.getTotalPrice()
if 0 < total_price:

  # Check that user has enough guarantee deposit to request a new service
  portal = context.getPortalObject()
  assert_price_kw = {
    'resource_uid': subscription_request.getPriceCurrencyUid(),
    'portal_type': portal.getPortalAccountingMovementTypeList(),
    'ledger_uid': portal.portal_categories.ledger.automated.getUid(),
  }

  deposit_amount = portal.portal_simulation.getInventoryAssetPrice(
    section_uid= subscription_request.getDestinationSectionUid(),
    mirror_section_uid= subscription_request.getSourceSectionUid(),
    mirror_node_uid=portal.restrictedTraverse('account_module/deposit').getUid(),
    #node_category_strict_membership=['account_type/income'],
    simulation_state= ('stopped', 'delivered'),
    #src__=1,
    **assert_price_kw
  )
  #return deposit_amount
  payable_amount = portal.portal_simulation.getInventoryAssetPrice(
    mirror_section_uid= subscription_request.getDestinationSectionUid(),
    section_uid= subscription_request.getSourceSectionUid(),
    # Do not gather deposit receivable
    # when it does not yet have a grouping_reference
    omit_asset_decrease=1,
    node_category_strict_membership=['account_type/asset/receivable',
                                     'account_type/liability/payable'],
    simulation_state= ('planned', 'confirmed', 'started', 'stopped', 'delivered'),
    grouping_reference=None,
    **assert_price_kw
  )

  # XXX what is the guarantee deposit account_type?
  if deposit_amount < payable_amount + total_price:

    # if not enough, user will have to pay a deposit for the subscription
    # XXX probably create an event asking for a deposit
    #pass
    return markHistory(subscription_request,
                      'Not enough deposit from user')
    # raise NotImplementedError('NO deposit_amount %s\npayable_amount %s\ntotal_price %s' % (deposit_amount, payable_amount, total_price))

#return 'YES deposit_amount %s\npayable_amount %s\ntotal_price %s' % (deposit_amount, payable_amount, total_price)
subscription_request.SubscriptionRequest_createOpenSaleOrder()
subscription_request.validate()
subscription_request.invalidate()
