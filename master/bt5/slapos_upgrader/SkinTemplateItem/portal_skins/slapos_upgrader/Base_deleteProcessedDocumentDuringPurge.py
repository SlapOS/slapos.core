from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

container = context.getParentValue()
container.manage_delObjects(ids=[context.getId()])
