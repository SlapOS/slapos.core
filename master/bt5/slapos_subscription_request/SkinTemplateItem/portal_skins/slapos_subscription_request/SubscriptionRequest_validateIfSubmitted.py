from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

subscription_request = context
portal = context.getPortalObject()
assert subscription_request.getPortalType() == 'Subscription Request'
assert subscription_request.getSimulationState() == 'submitted'

subscription_request.reindexObject(activate_kw=activate_kw)

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

if item.getValidationState() in ['invalidated', 'archived']:
  subscription_request.cancel(
    comment="%s is %s." % (item.getPortalType(), item.getValidationState()))
  return markHistory(subscription_request,
        'We cancelled your subscription request, the related instance was destroyed, invalidated or archived.')

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

  customer = subscription_request.getDestinationSectionValue()
  balance = customer.Entity_getDepositBalanceAmount([subscription_request])

  # XXX what is the guarantee deposit account_type?
  if balance < total_price:
    markHistory(subscription_request,
                'Your user does not have enough deposit.')

    # Check if a new trade condition has been created to
    # replace the existing one
    # (customer's service paid by an organisation)
    if item.getPortalType() == 'Project':
      project = item
    else:
      project = subscription_request.getSourceProjectValue()

    try:
      subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
        subscription_request.getDestinationValue(),
        # [software_type, software_release],
        subscription_request.getVariationCategoryList(),
        project,
        currency_value=subscription_request.getPriceCurrencyValue(),
        temp_object=True,
        item_value=item,
        causality_value=subscription_request.getCausalityValue()
      )
    except AssertionError:
      pass
    else:
      if subscription_change_request.getSpecialise() != subscription_request.getSpecialise():
        # We have a matching Trade Condition.
        # We can recreate the Subscription Request
        subscription_change_request = subscription_request.getResourceValue().Resource_createSubscriptionRequest(
          subscription_request.getDestinationValue(),
          # [software_type, software_release],
          subscription_request.getVariationCategoryList(),
          project,
          currency_value=subscription_request.getPriceCurrencyValue(),
          item_value=item,
          causality_value=subscription_request.getCausalityValue()
        )
        subscription_request.cancel(comment='Replaced by %s' % subscription_change_request.getReference())

    return

if subscription_request.checkConsistency():
  return markHistory(subscription_request,
    str(subscription_request.checkConsistency()[0].getTranslatedMessage()))

subscription_request.SubscriptionRequest_createOpenSaleOrder()
subscription_request.validate()
subscription_request.invalidate()
