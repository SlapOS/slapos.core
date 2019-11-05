from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

kw.update({
  'portal_type': 'Wechat Event',
  'source': portal.Base_getWechatServiceRelativeUrl(),
  'destination_value': context,
})

return portal.system_event_module.newContent(**kw)
