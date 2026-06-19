allocation_supply = context

assert allocation_supply.getPortalType() == 'Allocation Supply'

aggregate_value_list = allocation_supply.getAggregateValueList()
new_aggregate_value_list = [x for x in aggregate_value_list if x.getValidationState() != 'invalidated']

if len(aggregate_value_list) != len(new_aggregate_value_list):
  allocation_supply.edit(aggregate_value_list=new_aggregate_value_list)
  allocation_supply.reindexObject(activate_kw=activate_kw)

if (len(new_aggregate_value_list) == 0) and (allocation_supply.getValidationState() == 'validated'):
  allocation_supply.invalidate(comment='No linked node')
