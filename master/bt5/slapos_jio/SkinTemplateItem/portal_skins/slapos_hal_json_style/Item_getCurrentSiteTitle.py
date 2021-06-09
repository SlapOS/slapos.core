site = context.Item_getCurrentSiteValue(**kw)
if site is not None:
  return site.title
