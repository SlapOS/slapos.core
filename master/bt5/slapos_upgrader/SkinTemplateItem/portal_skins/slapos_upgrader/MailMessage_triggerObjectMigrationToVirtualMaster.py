from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

return context.WebMessage_triggerObjectMigrationToVirtualMaster(follow_up_relative_url)
