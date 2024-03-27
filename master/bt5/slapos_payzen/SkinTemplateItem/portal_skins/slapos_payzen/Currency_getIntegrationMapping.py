portal = context.getPortalObject()
relative_url = context.getRelativeUrl()

if relative_url == 'currency_module/CNY':
  integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredWechatIntegrationSite())
elif relative_url == 'currency_module/EUR':
  integration_site = portal.restrictedTraverse(portal.portal_preferences.getPreferredPayzenIntegrationSite())
else:
  # Only EUR is supported for now
  assert relative_url in ('currency_module/EUR', 'currency_module/CNY')

return integration_site.getMappingFromCategory('resource/%s' % relative_url).split('/', 1)[-1]
