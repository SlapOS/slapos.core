web_site = context.getWebSiteValue()
portal = context.getPortalObject()
from DateTime import DateTime

url = None

if web_site is not None:
  url = web_site.getLayoutProperty("configuration_slapos_master_web_url", default=None)

if url is not None and url != portal.absolute_url():
  description = "Please replace the url %s by %s on this feed url" % (portal.absolute_url(), url)
else:
  url = portal.absolute_url()
  description = "This RSS is disabled."

from Products.ERP5Type.Document import newTempBase

return [
       newTempBase(context, 'please_migrate', **{"title": "This RSS is disabled.",
                          "url_string": "%s?%s" % (url, DateTime().strftime("%Y%m%d")),
                          "modification_date": DateTime().earliestTime(),
                          "description": description})]
