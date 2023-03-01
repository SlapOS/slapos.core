from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredWechatIntegrationSite())

wechat_id = integration_site.getCategoryFromMapping('Causality/%s' % context.getId().replace('-', '_'))
if wechat_id != 'causality/%s' % context.getId().replace('-', '_'):
  # ok when using per day generator
  date = wechat_id.split('-', 1)[0]
  # and then switched to per day / per node generator
  date = date.split('.', 1)[0]
  return DateTime(date).toZone('UTC'), wechat_id
else:
  return None, None
