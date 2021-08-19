from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return context.Base_getNewsDictFromComputeNodeList(
  context.Project_getComputeNodeTrackingList())
