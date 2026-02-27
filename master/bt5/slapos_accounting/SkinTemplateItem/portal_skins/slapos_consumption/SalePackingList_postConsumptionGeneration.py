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
for sale_movement in sale_packing_list.getMovementList():
  sale_movement.edit(
    grouping_reference=grouping_reference,
    price=None,
  )
  if need_price:
    price = sale_movement.getPrice() or 0
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
