supply = context.getParentValue()
if (supply.getPortalType() != 'Consumption Supply') or (supply.getValidationState() != 'validated') or (supply.getAggregate(None) is None):
  return None

base_category_tuple = ('resource',)

for base_category in base_category_tuple:
  if context.getProperty(base_category) is None:
    return None

if supply.getDestination():
  base_category_tuple += ('destination',)

return context.generatePredicate(membership_criterion_base_category_list = base_category_tuple,
                                                 criterion_property_list = ('start_date',))
