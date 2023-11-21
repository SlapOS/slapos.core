from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
person = context

is_first_call = (tag is None)
tag = "%s_%s" % (person.getUid(), script.id)
activate_kw = {
  'tag': tag
}
wait_activate_kw = {
  'activity': 'SQLQueue',
  'serialization_tag': tag,
  'after_tag': tag
}

# Search the existing virtual master
virtual_master_title = 'Migrated personal for %s' % person.getTitle()
project = portal.portal_catalog.getResultValue(
  portal_type='Project',
  destination__uid=person.getUid(),
  title={'query': virtual_master_title, 'key': 'ExactMatch'}
)

if project is None:
  # Delay the script to prevent conflict with serialize
  # in the caller script
  # Prevent concurrent activities
  if is_first_call or (0 < portal.portal_activities.countMessageWithTag(tag)):
    return person.activate(**wait_activate_kw).Person_checkSiteMigrationCreatePersonalVirtualMaster(relative_url_to_migrate_list, tag=tag, *args, **kw)

  person.serialize()

  # No concurrent activity.
  # Create it
  project = person.Person_addVirtualMaster(
    title=virtual_master_title,
    is_compute_node_payable=False,
    is_instance_tree_payable=False,
    # Hardcoded
    price_currency='currency_module/EUR',
    batch=1,
    activate_kw=activate_kw
  )

# XXX Then, migrate other documents linked to the virtual master
for relative_url_to_migrate in relative_url_to_migrate_list:
  object_to_migrate = portal.restrictedTraverse(relative_url_to_migrate)
  object_to_migrate.activate().Base_activateObjectMigrationToVirtualMaster(project.getRelativeUrl())
