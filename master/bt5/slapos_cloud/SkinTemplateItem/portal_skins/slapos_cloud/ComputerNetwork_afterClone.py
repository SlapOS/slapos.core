if context.getPortalType() != "Computer Network":
  return

if context.getValidationState() == 'draft':
  context.setReference(None)
context.ComputerNetwork_init()
