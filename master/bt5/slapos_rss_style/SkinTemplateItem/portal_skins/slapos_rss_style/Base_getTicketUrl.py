web_site =  context.getWebSiteValue()

if not web_site:
  web_site = context.getPortalObject()

return web_site.absolute_url() + "/#/" + context.getRelativeUrl()
