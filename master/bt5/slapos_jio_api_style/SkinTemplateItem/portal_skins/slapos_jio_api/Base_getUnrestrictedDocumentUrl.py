if REQUEST:
  raise ValueError("This script should not be called directly")
# No need to get all results if an error is raised when at least 2 objects
# are found
l = context.getPortalObject().portal_catalog(limit=2, select_list=("relative_url",), **kw)
if len(l) != 1:
  return None
else:
  return l[0].relative_url
