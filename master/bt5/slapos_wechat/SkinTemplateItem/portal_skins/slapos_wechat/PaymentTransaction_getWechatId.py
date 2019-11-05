from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredWechatIntegrationSite())

wechat_id = integration_site.getCategoryFromMapping('Causality/%s' % context.getId().replace('-', '_'))
if wechat_id != 'causality/%s' % context.getId().replace('-', '_'):
  date, _ = wechat_id.split('-', 1)
  return DateTime(date).toZone('UTC'), wechat_id
else:
  return None, None
