from zExceptions import Unauthorized
from Products.ERP5Type.Core.Workflow import ValidationFailed
if REQUEST is not None:
  raise Unauthorized

portal = context.getPortalObject()

local_instance = context
compute_partition = local_instance.getAggregateValue()
if compute_partition is None:
  return
remote_node = compute_partition.getParentValue()
assert remote_node.getPortalType() == 'Remote Node'

remote_project = remote_node.getDestinationProjectValue(portal_type='Project')
remote_person = remote_node.getDestinationSectionValue(portal_type='Person')

# If local instance destruction has been propagated, do nothing
if local_instance.getValidationState() != 'validated':
  return

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
  return


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
    # Nothing can be done. Sadly, leave it as is for now.
    local_instance.setErrorStatus('No software release / type matching on the remote project')
    return
  else:
    upgrade_decision = remote_instance_tree.InstanceTree_createUpgradeDecision(
      target_software_release=new_release_variation,
      target_software_type=new_type_variation
    )
    if (upgrade_decision is None) and (portal.portal_catalog.getResultValue(
      portal_type='Upgrade Decision',
      aggregate__uid=remote_instance_tree.getUid(),
      simulation_state=['started', 'stopped', 'planned', 'confirmed']
    ) is None):
      local_instance.setErrorStatus('Can not upgrade the software release / type on the remote project')
    else:
      local_instance.setAccessStatus('Propagated')
    return upgrade_decision

if (remote_instance_tree is None) or \
  (remote_node.getSlaXml() != remote_instance_tree.getSlaXml()) or \
  (local_instance.getTextContent() != remote_instance_tree.getTextContent()) or \
  (local_instance.getSlapState() != remote_instance_tree.getSlapState()):

  try:
    remote_node.Base_checkConsistency()
  except ValidationFailed:
    local_instance.setErrorStatus("Can not propagate from inconsistent Remote Node")
    return

  remote_person.requestSoftwareInstance(
    project_reference=remote_project.getReference(),
    software_release=local_instance.getUrlString(),
    software_title='_remote_%s_%s' % (remote_node.getFollowUpReference(), local_instance.getReference()),
    software_type=local_instance.getSourceReference(),
    instance_xml=local_instance.getTextContent(),
    sla_xml=remote_node.getSlaXml(),
    shared=(local_instance.getPortalType() == 'Slave Instance'),
    state={'start_requested': 'started', 'stop_requested': 'stopped'}[local_instance.getSlapState()]
  )
  requested_software_instance = context.REQUEST.get('request_instance')
  requested_instance_tree = context.REQUEST.get('request_instance_tree')
  # Try to no trigger the script again on this object
  requested_instance_tree.reindexObject(activate_kw=activate_kw)
  if requested_software_instance is not None:
    requested_software_instance.reindexObject(activate_kw=activate_kw)
  local_instance.setAccessStatus('ok')

if (requested_software_instance is not None) and \
  (requested_software_instance.getConnectionXml() != local_instance.getConnectionXml()):
  # Try to no trigger the script again on this object
  local_instance.edit(
    connection_xml=requested_software_instance.getConnectionXml(),
    activate_kw=activate_kw
  )
  local_instance.setAccessStatus('ok')
