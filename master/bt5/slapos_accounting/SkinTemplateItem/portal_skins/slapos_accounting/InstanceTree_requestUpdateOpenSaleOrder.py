from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from DateTime import DateTime

portal = context.getPortalObject()
instance_tree = context

tag = '%s_%s' % (instance_tree.getUid(), script.id)
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return


def storeWorkflowComment(document, comment):
  portal.portal_workflow.doActionFor(document, 'edit_action', comment=comment)


def newOpenOrder():
  new_open_sale_order = portal.open_sale_order_module.newContent(
    portal_type="Open Sale Order",
    # XXX HARDCODED
    specialise=specialise,
    effective_date=DateTime(),
    activate_kw=activate_kw,
    destination=person.getRelativeUrl(),
    destination_decision=person.getRelativeUrl(),
    title="%s SlapOS Subscription" % person.getTitle()
  )

  new_open_sale_order.order(activate_kw=activate_kw)
  new_open_sale_order.validate(activate_kw=activate_kw)
  return new_open_sale_order

if instance_tree.getCausalityState() == 'diverged':
  person = instance_tree.getDestinationSectionValue(portal_type="Person")
  # Template document does not have person relation
  if person is not None:

    # Search an existing related open order
    open_order_line = portal.portal_catalog.getResultValue(
      portal_type='Open Sale Order Line',
      default_aggregate_uid=instance_tree.getUid())

    is_open_order_creation_needed = False

    # Simply check that it has never been simulated
    if instance_tree.getSlapState() == 'destroy_requested':
      # Line should be deleted
      if (open_order_line is not None) and (open_order_line.getValidationState() == "invalidated"):
        instance_tree.converge(comment="Last open order: %s" % open_order_line.getRelativeUrl())
      elif open_order_line is None:
        # User has no Open Sale Order (likely).
        # No need to charge, as it was never allocated
        is_open_order_creation_needed = False
        instance_tree.converge(comment="No open order needed as it was never allocated")

    elif open_order_line is None:
      # Let's add
      is_open_order_creation_needed = True

    # Let's create the open order
    if is_open_order_creation_needed:
      open_sale_order = newOpenOrder()

      open_order_explanation = ""
      # Add lines
      open_order_line = open_sale_order.newContent(
        portal_type="Open Sale Order Line",
        activate_kw=activate_kw
      )
      hosting_subscription = portal.hosting_subscription_module.newContent(
        portal_type="Hosting Subscription",
        title=instance_tree.getTitle()
      )
      hosting_subscription.validate()
      start_date = hosting_subscription.HostingSubscription_calculateSubscriptionStartDate()

      # Search for matching resource
      service_list = portal.portal_catalog(
        # XXX Hardcoded as temporary
        id='slapos_instance_subscription',
        portal_type='Service',
        validation_state='validated',
        use__relative_url='use/trade/sale'
      )
      service = [x for x in service_list if instance_tree.getPortalType() in x.getRequiredAggregatedPortalTypeList()][0].getObject()
      edit_kw = {
        'quantity': 1,
        'resource_value': service,
        'quantity_unit': service.getQuantityUnit(),
        'base_contribution_list': service.getBaseContributionList(),
        'use': service.getUse(),
        # XXX Hardcoded
        'price': 1
      }
      subscription_request = instance_tree.getAggregateRelatedValue(portal_type="Subscription Request")
      # Define the start date of the period, this can variates with the time.
      # start_date_delta = 0
      if subscription_request is not None:

        # Copy from Subscription Condition the source and Source Section into the line
        # RAFAEL: As the model is use single Open Order, it isn't possible to use multiple
        #  companies per region, so we rely on Subscription Conditions to Describe the
        #  providers.
        edit_kw["source"] = subscription_request.getSource()
        edit_kw["source_section"] = subscription_request.getSourceSection()

        # Quantity is double because the first invoice has to
        # charge for 2 months
        edit_kw['quantity'] = subscription_request.getQuantity()
        edit_kw['price'] = subscription_request.getPrice()
        edit_kw['price_currency'] = subscription_request.getPriceCurrency()
        # While create move the start date to be at least 1 months
        # So we can charge 3 months at once
        # You can increase 65 days to generate 3 months
        # You can increase 32 days to generate 2 months
        # You can increase 0 days to keep generating one month only
        # start_date_delta = 0

      open_order_line.edit(
        activate_kw=activate_kw,
        title=instance_tree.getTitle(),
        start_date=start_date,
        # Ensure stop date value is higher than start date
        # it will be updated by OpenSaleOrder_updatePeriod
        stop_date=start_date + 1,
        # stop_date=calculateOpenOrderLineStopDate(open_sale_order_line,
        #         instance_tree, start_date_delta=start_date_delta),
        aggregate_value_list=[hosting_subscription, instance_tree],
        **edit_kw
      )
      storeWorkflowComment(open_order_line, "Created for %s" % instance_tree.getRelativeUrl())
      # instance_tree.converge(comment="Last open order: %s" % open_sale_order_line.getRelativeUrl())
      open_order_explanation = "Added %s." % str(open_order_line.getId())

      storeWorkflowComment(open_sale_order, open_order_explanation)

    if open_order_line is not None:
      open_order = open_order_line.getParentValue()
      open_order.SaleOrder_applySaleTradeCondition(batch_mode=1)

      # Check compatibility with previous template
      assert open_order.getSourceSection() == 'organisation_module/slapos'
      assert open_order.getDestinationSection() == 'organisation_module/slapos'
      assert open_order.getSource() == 'organisation_module/slapos'
      assert open_order.getPriceCurrency() == 'currency_module/EUR'
      assert open_order.getSpecialise() == specialise

      assert open_order_line.getResource() == 'service_module/slapos_instance_subscription'
      assert open_order_line.getQuantityUnit() == 'unit/piece'
      assert open_order_line.getBaseContribution() == 'base_amount/invoicing/discounted'
      assert open_order_line.getBaseContributionList()[1] == 'base_amount/invoicing/taxable'
      assert open_order_line.getUse() == 'trade/sale'
      #assert open_order_line.getPrice() == 1, open_order_line.getPrice()
      #assert open_order_line.getQuantity() == 1

      open_order.OpenSaleOrder_updatePeriod()

    # Person_storeOpenSaleOrderJournal should fix all divergent Instance Tree in one run
    assert instance_tree.getCausalityState() == 'solved'
