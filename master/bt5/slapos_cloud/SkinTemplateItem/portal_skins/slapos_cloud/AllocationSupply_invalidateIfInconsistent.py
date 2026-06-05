allocation_supply = context

if allocation_supply.getValidationState() == 'validated':
  if len(allocation_supply.checkConsistency()) != 0:
    allocation_supply.invalidate()
