sale_packing_list = context
portal = context.getPortalObject()

# XXX grouping reference
grouping_reference = 'XXX'

"""
sale_packing_list_line.setGroupingReference(grouping_reference)
for internal_movement in internal_movement_list:
  internal_movement.setGroupingReference(grouping_reference)
  internal_movement.reindexObject(activate_kw=activate_kw)
"""
for tmp_movement in movement_list:
  internal_movement = portal.restrictedTraverse(tmp_movement.getSourceReference())
  internal_movement.edit(grouping_reference=grouping_reference)

need_price = not (
  (sale_packing_list.getSourceSection(None) == sale_packing_list.getDestinationSection(None)) or
  (sale_packing_list.getSourceSection(None) is None)
)
for sale_movement in sale_packing_list.getMovementList():
  sale_movement.edit(
    grouping_reference=grouping_reference,
    price=None,
  )
  price = sale_movement.getPrice() or 0

  if need_price:
    if not price:
      raise AssertionError('Can not find a price to generate the Consumption Packing List (%s) for %s' % (sale_packing_list.getSpecialiseValue(), sale_movement.getResource()))
  else:
    if price:
      raise AssertionError('Unexpected price while generating the Consumption Packing List (%s) for %s' % (sale_packing_list.getSpecialiseValue(), sale_movement.getResource()))

"""





  sale_packing_list.Delivery_fixBaseContributionTaxableRate()
  sale_packing_list.Base_checkConsistency()
  sale_packing_list.confirm()
  sale_packing_list.stop()
  sale_packing_list.deliver()
  sale_packing_list.reindexObject(activate_kw=activate_kw)
"""

sale_packing_list.Delivery_fixBaseContributionTaxableRate()
sale_packing_list.Base_checkConsistency()
return sale_packing_list.SalePackingList_postSlapOSGeneration(movement_list=movement_list)
