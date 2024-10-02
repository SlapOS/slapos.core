portal = context.getPortalObject()
monitor_enabled_category = portal.restrictedTraverse(
  "portal_categories/monitor_scope/enabled", None)

project = context.getFollowUpValue(portal_type='Project')
assert project is not None

if project.Project_isSupportRequestCreationClosed():
  return

if monitor_enabled_category is not None:
  project_uid = project.getUid()
  portal.portal_catalog.searchAndActivate(
    portal_type='Compute Node',
    validation_state='validated',
    monitor_scope__uid=monitor_enabled_category.getUid(),
    follow_up__uid=project_uid,
    method_id='ComputeNode_checkMonitoringState',
    # This alarm bruteforce checking all documents,
    # without changing them directly.
    # Increase priority to not block other activities
    activate_kw={'tag': tag, 'priority': 2}
  )

  portal.portal_catalog.searchAndActivate(
    # Slave is required due unallocated use case
    portal_type=['Software Instance', 'Slave Instance'],
    validation_state='validated',
    follow_up__uid=project_uid,
    group_by=['specialise_uid'],
    method_id='SoftwareInstance_checkInstanceTreeMonitoringState',
    # This alarm bruteforce checking all documents,
    # without changing them directly.
    # Increase priority to not block other activities
    activate_kw={'tag': tag, 'priority': 2}
  )

project.activate(after_tag=tag).getId()
