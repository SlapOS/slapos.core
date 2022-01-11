from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

result = context.OneTimeRestrictedAccessToken_getUserValue(REQUEST=REQUEST)
if result is not None:
  context.REQUEST.set('OneTimeVirtualMasterAccessToken_getProjectReference', context.getFollowUpReference(None))
return result
