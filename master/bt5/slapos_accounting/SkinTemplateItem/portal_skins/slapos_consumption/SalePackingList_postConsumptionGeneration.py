sale_packing_list = context
portal = context.getPortalObject()

grouping_reference = sale_packing_list.getReference()

causality_set = set()
for tmp_movement in movement_list:
  internal_movement = portal.restrictedTraverse(tmp_movement.getSourceReference())
  assert internal_movement.getGroupingReference() is None
  internal_movement.edit(grouping_reference=grouping_reference)
  causality_set.add(internal_movement.getExplanation())

need_price = not (
  (sale_packing_list.getSourceSection(None) == sale_packing_list.getDestinationSection(None)) or
  (sale_packing_list.getSourceSection(None) is None)
)

# Use the trade condition effective date to calculate the consumption price
# If a new Sale Supply is created, it will be effective only if
# a new Open Order version is generated too
# In short: use the consumption price which was configured when the user approved the open order
trade_condition = sale_packing_list.getSpecialiseValue(portal_type='Sale Trade Condition')
effective_date = trade_condition.getEffectiveDate(trade_condition.getCreationDate())

for sale_movement in sale_packing_list.getMovementList():
  sale_movement.edit(
    grouping_reference=grouping_reference,
    price=None,
  )
  if need_price:
    # Generate a temp movement with the date of the open order
    temp_sale_movement = sale_packing_list.newContent(
      portal_type='Sale Packing List Line',
      temp_object=True,
      start_date=effective_date,
      quantity=sale_movement.getQuantity(),
      category_list=sale_movement.getCategoryList()
    )
    price = temp_sale_movement.getPrice() or 0
  else:
    # Copy the logic of Resource_createSubscriptionRequest by not checking
    # Sale Supply if no price is needed
    price = 0

  if need_price:
    if not price:
      raise AssertionError('Can not find a price to generate the Consumption Packing List (%s) for %s' % (sale_packing_list.getSpecialiseValue(), sale_movement.getResource()))
  else:
    if price:
      raise AssertionError('Unexpected price while generating the Consumption Packing List (%s) for %s' % (sale_packing_list.getSpecialiseValue(), sale_movement.getResource()))

  sale_movement.edit(
    price=price,
  )

sale_packing_list.Delivery_fixBaseContributionTaxableRate()
sale_packing_list.Base_checkConsistency()
sale_packing_list.SalePackingList_postSlapOSGeneration(movement_list=movement_list)
# Set causality after, to prevent SalePackingList_postSlapOSGeneration to copy the Internal Packing List title
sale_packing_list.edit(
  causality_set=causality_set,
)
