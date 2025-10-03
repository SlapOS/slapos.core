instance = ([x for x in context.getSuccessorValueList(checked_permission='View') if (x.getTitle() == context.getTitle()) and (x.getSlapState() != 'destroy_requested')] + [None])[0]

if (portal_type is not None) and (instance is not None) and (instance.getPortalType() != portal_type):
  instance = None

return instance
