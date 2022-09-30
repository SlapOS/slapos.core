web_site = context.getWebSiteValue()

if web_site is None:
  # We must status
  prefix = ""
else:
  prefix = "[%s] " % web_site.getTitle()

prefix += "%s" % context.Base_translateString("Invoice")

start_date = context.getStartDate()
if start_date is not None:
  start_date = ' - (%s)' % context.getStartDate().strftime("%d/%m/%Y")
else:
  start_date = ''

return "%s %s%s" % (prefix,
  context.getReference(),
  start_date)
