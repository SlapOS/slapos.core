if context.getValidationState() != "validated":
  return 'Destroyed'

if context.getSlapState() == 'start_requested':
  return 'Installation requested'
else:
  return 'Destruction requested'
