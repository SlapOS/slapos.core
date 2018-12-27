from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return context.Base_getNewsDictFromComputerList(
  context.Organisation_getComputerTrackingList())
