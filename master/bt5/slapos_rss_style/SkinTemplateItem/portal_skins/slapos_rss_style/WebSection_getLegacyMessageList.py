from Products.PythonScripts.standard import Object
from DateTime import DateTime
from hashlib import md5
from Products.ERP5Type.Utils import str2bytes

portal = context.getPortalObject()
web_site = None
url = None

if context.getPortalType() in ["Web Site", "Web Section"]:
  web_site = context.getWebSiteValue()
  if web_site is not None:
    url = web_site.getLayoutProperty("configuration_slapos_master_web_url", default=None)

if url is not None and url != portal.absolute_url():
  description = "Please replace the url %s by %s on this feed url" % (portal.absolute_url(), url)
else:
  url = context.REQUEST.get('URL', context.absolute_url())
  description = """
This RSS feed is disabled:

  %s?...

Please remove it from your RSS reader, and use the global feed instead in order to get updates.
""" % url

# Use date to ensure it changes every day.
date_id = DateTime().strftime("%Y%m%d")

return [Object(**{
          'title': "This RSS is disabled (%s)" % date_id,
          'category': 'Disabled',
          'author': 'Administrator',
          'link': "%s?date=%s" % (url, date_id),
          'pubDate': DateTime().earliestTime(),
          'guid': md5(str2bytes("%s-%s" % (url, date_id))).hexdigest(),
          'description': description,
          'thumbnail': ( None)})
        ]
