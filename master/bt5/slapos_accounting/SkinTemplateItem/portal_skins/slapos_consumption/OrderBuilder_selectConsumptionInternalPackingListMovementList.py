from erp5.component.module.DateUtils import addToDate

portal = context.getPortalObject()

subscribed_item_resource_dict = {}
now = DateTime()

for (_, brain) in enumerate(portal.portal_simulation.getInventoryList(
  simulation_state='delivered',
  portal_type=['Internal Packing List Line',
               'Internal Packing List Cell'],
  parent__ledger__uid=portal.portal_categories.ledger.automated.getUid(),
  grouping_reference=None,
  # Consumption must be added to the user invoice
  # as soon as possible (on the next user invoicing period)
  # even if the consumption period is not finished
  # This should prevent cases where invoice get the consumption for a destroyed service
  from_date=addToDate(now, {'month': -2}),
)):

  internal_movement = brain.getObject()
  # no variation is expected for now
  assert internal_movement.getPortalType() != 'Internal Packing List Cell'
  assert internal_movement.getGroupingReference(None) is None
  item = ([x for x in internal_movement.getAggregateValueList() if x.getPortalType() != 'Consumption Subscription'] or [None])[0]
  if item is None:
    raise ValueError('Unexpected movement without item: %s' % internal_movement.getRelativeUrl())

  #########################################################
  # Search for the related project
  # and the related item used on open order (to decide on which invoice we want to link the consumption)
  item_portal_type = item.getPortalType()

  if item_portal_type in ('Software Instance', 'Slave Instance', 'Compute Node'):
    item_project = item.getFollowUpValue(portal_type='Project')
    # If not project is defined, the data seems in bad shape
    # assert item_project.getPortalType() == 'Project'
  else:
    raise ValueError('Unexpected item portal type: %s on %s' % (item_portal_type, internal_movement.getRelativeUrl()))

  internal_packing_list = internal_movement.getParentValue()
  assert internal_packing_list.getPortalType() == 'Internal Packing List'
  causality_portal_type = internal_packing_list.getCausalityValue().getPortalType()
  if causality_portal_type == 'Computer Consumption TioXML File':
    # Instances usage are paid by the instance owner
    subscribed_item = item.getSpecialiseValue(portal_type='Instance Tree')
    # Data is not consistent
    # assert subscribed_item.getPortalType() == 'Instance Tree'
  elif causality_portal_type == 'Consumption Subscription':
    # Subscription for Instances/Node are paid by the project owner
    subscribed_item = item_project
  else:
    raise ValueError('Unsupported causality value: %s' % internal_packing_list.getCausality())


  if subscribed_item is None:
    # It is not possible to find the related Open Order
    continue

  subscribed_item_resource_dict.setdefault(subscribed_item.getRelativeUrl(), {})
  subscribed_item_resource_dict[subscribed_item.getRelativeUrl()].setdefault(internal_movement.getResource(), [])
  subscribed_item_resource_dict[subscribed_item.getRelativeUrl()][internal_movement.getResource()].append(internal_movement)

tmp_movement_list = []

for subscribed_item_relative_url, resource_dict in subscribed_item_resource_dict.items():
  subscribed_item = portal.restrictedTraverse(subscribed_item_relative_url)

  #########################################################
  # Search for the related project
  # and the related item used on open order (to decide on which invoice we want to link the consumption)
  # If no open order, subscription must be approved
  open_order_movement_list = portal.portal_catalog(
    portal_type=['Open Sale Order Line', 'Open Sale Order Cell'],
    aggregate__uid=subscribed_item.getUid(),
    # validation_state='validated',
    sort_on=[('creation_date', 'DESC')],
    limit=1
  )
  if len(open_order_movement_list) == 0:
    continue

  open_sale_order = open_order_movement_list[0]
  while open_sale_order.getPortalType() != 'Open Sale Order':
    open_sale_order = open_sale_order.getParentValue()

  hosting_subscription = open_order_movement_list[0].getAggregateValue(portal_type='Hosting Subscription')
  start_date = open_sale_order.getStartDate()
  next_period_date = hosting_subscription.getNextPeriodicalDate(now)
  # Calculate the start_date of the monthly packing list
  previous_period_date = start_date
  while hosting_subscription.getNextPeriodicalDate(previous_period_date) < next_period_date:
    previous_period_date = hosting_subscription.getNextPeriodicalDate(previous_period_date)

  if now + 1 < next_period_date:
    # Wait as much as possible before aggregating the consumption
    # in order to reduce the number of Sale Packing List created
    # and reduce the number of invoice lines
    continue

  #################################################################
  # Accumulate lines
  for resource_relative_url, internal_movement_list in resource_dict.items():
    for internal_movement in internal_movement_list:

      tmp_movement_list.append(portal.portal_trash.newContent(
        portal_type='Sale Packing List Line',
        temp_object=1,
        # Keep track of the original movement
        # In order to set a grouping reference after the build
        source_reference=internal_movement.getRelativeUrl(),

        title='Consumption %s for %s' % (previous_period_date, subscribed_item.getTitle()),
        start_date=previous_period_date,
        # It should match the first open order invoice
        stop_date=next_period_date,
        specialise_value=open_sale_order.getSpecialiseValue(),
        source_value=open_sale_order.getSourceValue(),
        source_section_value=open_sale_order.getSourceSectionValue(),
        source_decision_value=open_sale_order.getSourceDecisionValue(),
        source_project_value=open_sale_order.getSourceProjectValue(),
        destination_value=open_sale_order.getDestinationValue(),
        destination_section_value=open_sale_order.getDestinationSectionValue(),
        destination_decision_value=open_sale_order.getDestinationDecisionValue(),
        destination_project_value=open_sale_order.getDestinationProjectValue(),
        ledger_value=open_sale_order.getLedgerValue(),
        # XXX experiment to trigger Alarm_updateSlapOSDeliverySimulation
        causality_value=open_sale_order,
        price_currency_value=open_sale_order.getPriceCurrencyValue(),

        resource=resource_relative_url,
        #variation_category_list=variation_category_list,
        quantity_unit_value=internal_movement.getQuantityUnitValue(),
        base_contribution_list=internal_movement.getBaseContributionList(),
        use=internal_movement.getUse(),
        quantity=internal_movement.getQuantity(),
        # quantity=sum([x.getQuantity() for x in internal_movement_list]),
        price=0,
        # XXX Check the price
        #price=internal_movement.getPrice(),
        # no item, as this movement is the sum of many others
        #aggregate_value_list=[],
      ))



  """
  # XXX XXX See OpenSaleOrderCell_createDiscountSalePackingList
  sale_packing_list = portal.sale_packing_list_module.newContent(
    portal_type='Sale Packing List',
    title='Consumption %s for %s' % (previous_period_date, subscribed_item.getTitle()),
    start_date=previous_period_date,
    # It should match the first open order invoice
    stop_date=next_period_date,
    specialise_value=open_sale_order.getSpecialiseValue(),
    source_value=open_sale_order.getSourceValue(),
    source_section_value=open_sale_order.getSourceSectionValue(),
    source_decision_value=open_sale_order.getSourceDecisionValue(),
    source_project_value=open_sale_order.getSourceProjectValue(),
    destination_value=open_sale_order.getDestinationValue(),
    destination_section_value=open_sale_order.getDestinationSectionValue(),
    destination_decision_value=open_sale_order.getDestinationDecisionValue(),
    destination_project_value=open_sale_order.getDestinationProjectValue(),
    ledger_value=open_sale_order.getLedgerValue(),
    # XXX experiment to trigger Alarm_updateSlapOSDeliverySimulation
    causality_value=open_sale_order,
    price_currency_value=open_sale_order.getPriceCurrencyValue(),
    # activate_kw=activate_kw
  )

  #################################################################
  # Accumulate lines
  for resource_relative_url, internal_movement_list in resource_dict.items():
    internal_movement = internal_movement_list[0]
    sale_packing_list_line = sale_packing_list.newContent(
      # no variation is expected for now
      portal_type='Sale Packing List Line',
      resource=resource_relative_url,
      #variation_category_list=variation_category_list,
      quantity_unit_value=internal_movement.getQuantityUnitValue(),
      base_contribution_list=internal_movement.getBaseContributionList(),
      use=internal_movement.getUse(),
      quantity=sum([x.getQuantity() for x in internal_movement_list]),
      # XXX Check the price
      #price=internal_movement.getPrice(),
      # no item, as this movement is the sum of many others
      #aggregate_value_list=[],
    )
    #raise NotImplementedError(str(brain))
  """

return tmp_movement_list
