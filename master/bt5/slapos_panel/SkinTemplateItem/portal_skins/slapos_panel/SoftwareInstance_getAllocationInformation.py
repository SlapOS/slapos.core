if context.getAggregate() is None:
  return context.Base_translateString("Not allocated")

partition = context.getAggregateValue(checked_permission="View")
if partition is not None:
  allocation_information = "%s (%s)" % (
    partition.getParentValue().getReference(), 
    partition.getReference())
  network_title = partition.getParentValue().getSubordinationTitle(checked_permission="View")
  if network_title is not None:
    allocation_information += " - %s" % network_title
  return allocation_information

return context.Base_translateString("Restricted information")
