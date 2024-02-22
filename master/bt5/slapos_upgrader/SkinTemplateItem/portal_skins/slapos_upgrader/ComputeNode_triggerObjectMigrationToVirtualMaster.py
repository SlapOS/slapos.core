from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
compute_node = context
project = portal.restrictedTraverse(project_relative_url)

edit_kw = {}

# Check if it has been migrated first
if compute_node.getFollowUpValue() is None:
  edit_kw['follow_up_value'] = project

if compute_node.getAllocationScope('').startswith('open/'):
  edit_kw['allocation_scope'] = 'open'


# Migrate
if edit_kw:
  compute_node.edit(**edit_kw)

# Drop outdated categories
category_list = compute_node.getCategoryList()
new_category_list = [x for x in category_list if not x.startswith('source_administration')]

if len(category_list) != len(new_category_list):
  compute_node.setCategoryList(new_category_list)

# Trigger migrations of related objects
not_migrated_select_dict={'default_follow_up_uid': None}
portal.portal_catalog.searchAndActivate(
  method_id='Base_activateObjectMigrationToVirtualMaster',
  method_args=[project_relative_url],

  portal_type='Software Installation',
  aggregate__uid=compute_node.getUid(),
  select_dict=not_migrated_select_dict,
  left_join_list=not_migrated_select_dict.keys(),
  **not_migrated_select_dict
)
