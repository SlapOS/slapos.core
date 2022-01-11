if (not context.hasBasePrice()) or (not context.getPriceCurrency()) or (not context.getResource()) or (not context.getQuantityUnit()):
  # Meaningless path if no resource/price_currency/base_price/quantity_unit
  return None

supply = context.getParentValue()

base_category_tuple = ['resource', 'price_currency', 'quantity_unit']
if context.getPortalType() == 'Sale Supply Cell':
  base_category_tuple.extend(supply.getVariationRangeBaseCategoryList())
  supply = supply.getParentValue()

if (supply.getPortalType() != 'Sale Supply') or (supply.getValidationState() != 'validated'):
  # If this supply line is not in a validated Sale Supply, it does not apply.
  return None

if context.getSourceSection():
  base_category_tuple.append('source_section')
if context.getDestinationSection():
  base_category_tuple.append('destination_section')

if context.getSource():
  base_category_tuple.append('source')
if context.getDestination():
  base_category_tuple.append('destination')

if context.getSourceProject():
  base_category_tuple.append('source_project')
if context.getDestinationProject():
  base_category_tuple.append('destination_project')

#backwards compatibility
mapped_value_property_list = context.getMappedValuePropertyList()
for mapped_property in ('priced_quantity', 'quantity_unit'):
  if not mapped_property in mapped_value_property_list:
    mapped_value_property_list.append(mapped_property)
    context.setMappedValuePropertyList(mapped_value_property_list)

return context.generatePredicate(membership_criterion_base_category_list = base_category_tuple,
                                                 criterion_property_list = ('start_date',))
