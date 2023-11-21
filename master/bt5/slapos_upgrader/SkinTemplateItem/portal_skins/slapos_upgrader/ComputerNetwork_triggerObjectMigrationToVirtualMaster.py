from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
computer_network = context
project = portal.restrictedTraverse(project_relative_url)

edit_kw = {}

# Check if it has been migrated first
if computer_network.getFollowUpValue() is None:
  edit_kw['follow_up_value'] = project

# Migrate
if edit_kw:
  computer_network.edit(**edit_kw)

# Drop outdated categories
category_list = computer_network.getCategoryList()
new_category_list = [x for x in category_list if not x.startswith('source_administration')]

if len(category_list) != len(new_category_list):
  computer_network.setCategoryList(new_category_list)
