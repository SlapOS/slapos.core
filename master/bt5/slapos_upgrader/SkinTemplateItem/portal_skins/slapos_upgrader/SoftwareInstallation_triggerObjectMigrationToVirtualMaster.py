from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
software_installation = context
project = portal.restrictedTraverse(project_relative_url)

edit_kw = {}

# Check if it has been migrated first
if software_installation.getFollowUpValue() is None:
  edit_kw['follow_up_value'] = project

# Migrate
if edit_kw:
  software_installation.edit(**edit_kw)

# Drop outdated categories
category_list = software_installation.getCategoryList()
new_category_list = [x for x in category_list if not x.startswith('destination_section')]

if len(category_list) != len(new_category_list):
  software_installation.setCategoryList(new_category_list)
