from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

compute_partition = context
remote_node = compute_partition.getParentValue()
assert remote_node.getPortalType() == 'Remote Node'

remote_project = remote_node.getDestinationProjectValue(portal_type='Project')
remote_person = remote_node.getDestinationSectionValue(portal_type='Person')

if local_instance_list is None:
  if compute_partition.getId() == 'SHARED_REMOTE':
    # Hardcoded ID behaviour
    local_instance_list = portal.portal_catalog(
      portal_type='Slave Instance',
      aggregate__uid=compute_partition.getUid(),
      validation_state='validated'
    )

  else:
    local_instance_list = portal.portal_catalog(
      portal_type='Software Instance',
      aggregate__uid=compute_partition.getUid(),
      validation_state='validated'
    )
else:
  local_instance_list = [portal.restrictedTraverse(x) for x in local_instance_list]

for local_instance in local_instance_list:
  assert local_instance.getAggregate() == compute_partition.getRelativeUrl()

  # If local instance destruction has been propagated, do nothing
  if local_instance.getValidationState() != 'validated':
    continue

  # do not increase the workflow history
  # Use the 'cached' API instead
  # manually search the instance and compare all parameters
  remote_instance_tree = portal.portal_catalog.getResultValue(
    portal_type='Instance Tree',
    validation_state='validated',
    destination_section__uid=remote_person.getUid(),
    follow_up__uid=remote_project.getUid(),
    title={'query': '_remote_%s_%s' % (local_instance.getFollowUpReference(),
                                       local_instance.getReference()),
           'key': 'ExactMatch'}
  )

  if remote_instance_tree is not None:
    requested_software_instance = remote_instance_tree.getSuccessorValue(title=remote_instance_tree.getTitle())

  if (local_instance.getSlapState() == 'destroy_requested'):
    if (remote_instance_tree is not None) and \
      (remote_instance_tree.getSlapState() != 'destroy_requested'):
      # if local instance is destroyed, propagate blindly (do not check url, text content, ...)
      remote_person.requestSoftwareInstance(
        project_reference=remote_project.getReference(),
        software_release=remote_instance_tree.getUrlString(),
        software_title='_remote_%s_%s' % (remote_node.getFollowUpReference(), local_instance.getReference()),
        software_type=remote_instance_tree.getSourceReference(),
        instance_xml=remote_instance_tree.getTextContent(),
        sla_xml=None,
        shared=(local_instance.getPortalType() == 'Slave Instance'),
        state='destroyed'
      )
      remote_instance_tree.reindexObject(activate_kw=activate_kw)
    local_instance.invalidate(comment='Remote destruction has been propagated')
    # Try to no trigger the script again on this object
    local_instance.reindexObject(activate_kw=activate_kw)
    continue


  if (remote_instance_tree is not None) and \
    ((local_instance.getUrlString() != remote_instance_tree.getUrlString()) or \
     (local_instance.getSourceReference() != remote_instance_tree.getSourceReference())):
    # Try to create an Upgrade Decision for the new release
    # XXX Move this code to InstanceTree_createUpgradeDecision, and pass only string arguments to it
    _, new_release_variation, new_type_variation = remote_instance_tree.asContext(
      url_string=local_instance.getUrlString(),
      source_reference=local_instance.getSourceReference()
    ).InstanceTree_getSoftwareProduct()
    if new_release_variation is None:
      return
    else:
      return remote_instance_tree.InstanceTree_createUpgradeDecision(
        target_software_release=new_release_variation,
        target_software_type=new_type_variation
      )

  if (remote_instance_tree is None) or \
    (local_instance.getTextContent() != remote_instance_tree.getTextContent()) or \
    (local_instance.getSlapState() != remote_instance_tree.getSlapState()):

    remote_person.requestSoftwareInstance(
      project_reference=remote_project.getReference(),
      software_release=local_instance.getUrlString(),
      software_title='_remote_%s_%s' % (remote_node.getFollowUpReference(), local_instance.getReference()),
      software_type=local_instance.getSourceReference(),
      instance_xml=local_instance.getTextContent(),
      sla_xml=None,
      shared=(local_instance.getPortalType() == 'Slave Instance'),
      state={'start_requested': 'started', 'stop_requested': 'stopped'}[local_instance.getSlapState()]
    )
    requested_software_instance = context.REQUEST.get('request_instance')
    requested_instance_tree = context.REQUEST.get('request_instance_tree')
    # Try to no trigger the script again on this object
    requested_instance_tree.reindexObject(activate_kw=activate_kw)
    if requested_software_instance is not None:
      requested_software_instance.reindexObject(activate_kw=activate_kw)

  if (requested_software_instance is not None) and \
    (requested_software_instance.getConnectionXml() != local_instance.getConnectionXml()):
    # Try to no trigger the script again on this object
    local_instance.edit(
      connection_xml=requested_software_instance.getConnectionXml(),
      activate_kw=activate_kw
    )
