title = context.getTitle()
result = []
found = False
for instance in context.getSuccessorValueList(checked_permission='View'):
  if (instance.getTitle() == title) and (instance.getSlapState() != 'destroy_requested'):
    found = True
    break

if found:
  result = instance.SoftwareInstance_getConnectionParameterList(
               relative_url=context.getRelativeUrl(), raw=raw)

return result
