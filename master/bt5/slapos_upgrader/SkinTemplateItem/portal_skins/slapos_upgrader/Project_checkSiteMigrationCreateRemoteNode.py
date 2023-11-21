from zExceptions import Unauthorized

if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()
project = context

is_first_call = (tag is None)
tag = "%s_%s_%s" % (project.getUid(), script.id, remote_project_relative_url)
activate_kw = {
  'tag': tag
}
wait_activate_kw = {
  'activity': 'SQLQueue',
  'serialization_tag': tag,
  'after_tag': tag
}

remote_project = portal.restrictedTraverse(remote_project_relative_url)

# Search the existing virtual master
remote_node_title = 'Migrated remote to %s' % remote_project.getReference()

remote_node = portal.portal_catalog.getResultValue(
  portal_type='Remote Node',
  destination_project__uid=remote_project.getUid(),
  follow_up__uid=project.getUid(),
  title={'query': remote_node_title, 'key': 'ExactMatch'}
)

if remote_node is None:
  # Delay the script to prevent conflict with serialize
  # in the caller script
  # Prevent concurrent activities
  if is_first_call or (0 < portal.portal_activities.countMessageWithTag(tag)):
    return project.activate(**wait_activate_kw).Project_checkSiteMigrationCreateRemoteNode(remote_project_relative_url, relative_url_to_migrate_list, tag=tag, *args, **kw)

  project.serialize()

  # No concurrent activity.
  # Create it
  # XXX copied from Project_addSlapOSRemoteNode
  remote_node = portal.compute_node_module.newContent(
    portal_type='Remote Node',
    title=remote_node_title,
    # Use the project owner
    destination_section_value=remote_project.getDestinationValue(),
    destination_project_value=remote_project,
    follow_up_value=project,
    allocation_scope='open',
    activate_kw=activate_kw
  )
  remote_node.validate()
  remote_node.reindexObject(activate_kw=activate_kw)


# XXX Then, migrate other documents linked to the virtual master
portal.portal_catalog.searchAndActivate(
  method_id='Base_activateObjectMigrationToRemoteVirtualMaster',
  method_args=[remote_node.getRelativeUrl()],
  activate_kw=activate_kw,

  # Go slowly, because it generate DB conflicts
  packet_size=1,
  activity_count=1000,

  relative_url=relative_url_to_migrate_list,
)
