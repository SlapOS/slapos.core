from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
instance_tree = context
project = portal.restrictedTraverse(project_relative_url)

edit_kw = {}

# Check if it has been migrated first
if instance_tree.getFollowUpValue() is None:
  edit_kw['follow_up_value'] = project

# Migrate
if edit_kw:
  instance_tree.edit(**edit_kw)

# Trigger migrations of related objects
portal.portal_catalog.searchAndActivate(
  method_id='Base_activateObjectMigrationToVirtualMaster',
  method_args=[project_relative_url],

  portal_type=['Software Instance', 'Slave Instance'],
  specialise__uid=instance_tree.getUid()
)
