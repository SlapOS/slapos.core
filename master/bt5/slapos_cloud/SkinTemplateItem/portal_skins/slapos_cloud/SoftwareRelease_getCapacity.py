software_release = context

software_product = software_release.getAggregateValue()
software_release_capacity = software_product.getCapacityQuantity(None)

if software_release_capacity is None:
  software_release_capacity = software_release.getCapacityQuantity(1)

return software_release_capacity
