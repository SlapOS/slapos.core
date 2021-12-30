from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return context.getAccessStatus()
