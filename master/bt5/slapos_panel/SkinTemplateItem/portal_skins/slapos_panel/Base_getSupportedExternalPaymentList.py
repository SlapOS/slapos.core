from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

# Keep a simple list so we can extend/reduce until we have a proper configuration 
# mapping for this.
return [
  (portal.currency_module.EUR.getUid(), portal.Base_getPayzenServiceRelativeUrl()),
  # (portal.currency_module.CNY.getUid(), portal.Base_getWechatServiceRelativeUrl())
  ]
