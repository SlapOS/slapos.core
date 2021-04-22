web_site = context.getWebSiteValue()

if web_site is None:
  # We must status
  prefix = ""
else:
  prefix = "[%s] " % web_site.getTitle()

prefix += "%s" % context.Base_translateString("Invoice")

return "%s %s - (%s)" % (prefix,
  context.getReference(),
  context.getStartDate().strftime("%d/%m/%Y"))
