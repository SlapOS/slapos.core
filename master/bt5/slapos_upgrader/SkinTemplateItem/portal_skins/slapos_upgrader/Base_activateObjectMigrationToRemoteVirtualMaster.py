from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

return context.getTypeBasedMethod('triggerObjectMigrationToRemoteVirtualMaster')(project_relative_url)
