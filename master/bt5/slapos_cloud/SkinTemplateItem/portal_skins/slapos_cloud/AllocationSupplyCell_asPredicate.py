line = context.getParentValue()
supply = line.getParentValue()
if (supply.getPortalType() != 'Allocation Supply') or (supply.getValidationState() != 'validated') or (supply.getAggregate(None) is None):
  return None

if not context.isAllocable():
  return None

base_category_tuple = ('resource', 'software_type', 'software_release', 'destination_project')

for base_category in base_category_tuple:
  if context.getProperty(base_category) is None:
    return None

if supply.getDestination():
  base_category_tuple += ('destination',)


return context.generatePredicate(membership_criterion_base_category_list = base_category_tuple,
                                                 criterion_property_list = ('start_date',))
