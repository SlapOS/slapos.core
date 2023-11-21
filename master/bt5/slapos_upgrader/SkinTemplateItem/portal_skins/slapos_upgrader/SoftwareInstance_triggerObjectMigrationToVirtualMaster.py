from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
software_instance = context
project = portal.restrictedTraverse(project_relative_url)

edit_kw = {}

# Check if it has been migrated first
if software_instance.getFollowUpValue() is None:
  edit_kw['follow_up_value'] = project

# Migrate
if edit_kw:
  software_instance.edit(**edit_kw)
