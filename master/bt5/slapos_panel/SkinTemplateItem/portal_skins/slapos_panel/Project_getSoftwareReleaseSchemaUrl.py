from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

# Ensure this script is called on the expected context
# for futur compatibility
assert context.getPortalType() == 'Project'

return software_release_url.split("?")[0] + ".json"
