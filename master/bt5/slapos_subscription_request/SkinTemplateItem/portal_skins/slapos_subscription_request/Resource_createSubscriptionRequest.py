portal = context.getPortalObject()
resource = context

if (subscriber_person_value is None) or (subscriber_person_value.getPortalType() != 'Person'):
  raise AssertionError('%s is not a person profile' % subscriber_person_value)

source_project_value = None
destination_project_value = None
forced_trade_condition_type = trade_condition_type

if resource.getPortalType() == "Software Product":
  source_project_value = project_value

  trade_condition_type = "instance_tree"
  if not temp_object:
    assert item_value is not None
    assert item_value.getPortalType() == 'Instance Tree'

elif resource.getPortalType() == "Service":
  if resource.getRelativeUrl() == "service_module/slapos_compute_node_subscription":
    if project_value is None:
      raise AssertionError('A project is required for %s %s' % (resource.getRelativeUrl(), project_value))
    source_project_value = project_value

    trade_condition_type = "compute_node"
    if not temp_object:
      assert item_value is not None
      assert item_value.getPortalType() == 'Compute Node'

  elif resource.getRelativeUrl() == "service_module/slapos_virtual_master_subscription":
    if project_value is None:
      raise AssertionError('Project is required for %s %s' % (resource.getRelativeUrl(), project_value))
    if item_value is not None:
      assert project_value.getRelativeUrl() == item_value.getRelativeUrl()
    item_value = project_value
    trade_condition_type = "virtual_master"
  else:
    raise NotImplementedError('Unsupported resource: %s' % resource.getRelativeUrl())
else:
  raise NotImplementedError('Unsupported resource: %s' % resource.getRelativeUrl())

if forced_trade_condition_type is not None:
  # explicit trade_condition_type was provided
  trade_condition_type = forced_trade_condition_type

######################################################
# Find Sale Trade Condition and price

# Create a temp Sale Order to calculate the real price and find the trade condition
now = DateTime()
module = portal.portal_trash
#aggregate_value_list = []

tmp_sale_order = module.newContent(
  portal_type='Sale Order',
  temp_object=True,
  trade_condition_type=trade_condition_type,
  start_date=now,
  destination_value=subscriber_person_value,
  # Do NOT use destination_section to search the trade condition
  # as trade condition will be used to decide who will pay
  #destination_decision_value=source_decision_value,
  destination_project_value=destination_project_value,
  source_project_value=source_project_value,
  ledger_value=portal.portal_categories.ledger.automated,
  # XXX XXX destination_project_value=instance_tree.getFollowUpValue(),
  price_currency_value=currency_value
)
tmp_sale_order.SaleOrder_applySaleTradeCondition(batch_mode=1, force=1)

if tmp_sale_order.getSpecialise(None) is None:
  raise AssertionError('Can not find a trade condition to generate the Subscription Request')

if tmp_sale_order.getTradeConditionType() != tmp_sale_order.getSpecialiseValue().getTradeConditionType():
  raise AssertionError('Unexpected different trade_condition_type: %s %s' % (tmp_sale_order.getTradeConditionType(), tmp_sale_order.getSpecialiseValue().getTradeConditionType()))

if currency_value is not None:
  if currency_value.getRelativeUrl() != tmp_sale_order.getPriceCurrency():
    raise AssertionError('Unexpected different currency: %s %s' % (currency_value.getRelativeUrl(), tmp_sale_order.getPriceCurrency()))

# If no accounting is needed, no price is expected
if (tmp_sale_order.getSourceSection(None) == tmp_sale_order.getDestinationSection(None)) or \
  (tmp_sale_order.getSourceSection(None) is None):
  price = default_price or 0
  if price:
    raise AssertionError('Unexpected price %s found to generate the Subscription Request (%s)' % (price, tmp_sale_order.getSpecialise()))
else:

  # Add line
  tmp_order_line = tmp_sale_order.newContent(
    portal_type='Sale Order Line',
    temp_object=True,
    resource_value=resource,
    variation_category_list=variation_category_list,
    quantity_unit=resource.getQuantityUnit(),
    base_contribution_list=resource.getBaseContributionList(),
    use=resource.getUse(),
    quantity=1
  )

  if variation_category_list:
    base_id = 'movement'
    cell_key = list(tmp_order_line.getCellKeyList(base_id=base_id))[0]
    tmp_order_cell = tmp_order_line.newCell(
      base_id=base_id,
      portal_type='Sale Order Cell',
      temp_object=True,
      *cell_key
    )

    tmp_order_cell.edit(
      mapped_value_property_list=['price','quantity'],
      quantity=1,
      predicate_category_list=cell_key,
      variation_category_list=cell_key
    )
    price = tmp_order_cell.getPrice() or default_price or 0
  else:
    price = tmp_order_line.getPrice() or default_price or 0


  # but if accounting is needed, we expect a price
  if not price:
    raise AssertionError('Can not find a price to generate the Subscription Request (%s)' % tmp_sale_order.getSpecialiseValue())

subscription_request = portal.getDefaultModuleValue(portal_type).newContent(
  portal_type=portal_type,
  temp_object=temp_object,
  destination_value=subscriber_person_value,
  # Do not set a default destination section if it is not defined on a trade condition
  # this will allow Sale Manager to review the subscription (to fill address, maybe create an organisation)
  # and maybe even create a trade condition for the customer
  # WARNING: do NOT use career_subordination. It is unrelated to who will pay.
  #          subordination is used for payroll only.
  #          Who pays comes from the trade conditions if needed.
  # XXX TODO
  destination_section=tmp_sale_order.getDestinationSection(subscriber_person_value.getRelativeUrl()),
  destination_decision_value=subscriber_person_value,
  destination_project_value=destination_project_value,
  start_date=now,
  effective_date=now,
  resource_value=resource,
  variation_category_list=variation_category_list,
  aggregate_value=item_value,
  quantity_unit=resource.getQuantityUnit(),
  quantity=1,
  ledger="automated",
  specialise_value=tmp_sale_order.getSpecialiseValue(),
  source=tmp_sale_order.getSource(),
  source_section=tmp_sale_order.getSourceSection(),
  source_project_value=source_project_value,
  price_currency=tmp_sale_order.getPriceCurrency(),
  price=price,
  # XXX activate_kw=activate_kw
  causality_value=causality_value,
)
if temp_object:
  subscription_request.edit(reference="foo")

if not temp_object:
  subscription_request.submit()

return subscription_request
