compute_partition = context

compute_node = compute_partition.getParentValue()
assert compute_node.getPortalType() == 'Compute Node'

instance = compute_partition.getAggregateRelatedValue(portal_type='Software Instance')
assert instance is not None, 'Instance is None'
assert instance.getValidationState() != 'validated', 'Instance is invalid'

sla_error_list = []
sla_dict = instance.getSlaXmlAsDict()
if not sla_dict:
  return sla_error_list

# Simple check of instance SLAs
if "computer_guid" in sla_dict:
  computer_guid = sla_dict.pop("computer_guid")
  if compute_node.getReference() != computer_guid:
    sla_error_list.append('computer_guid do not match (%s != %s)' % (
      computer_guid, compute_node.getReference()))

if "instance_guid" in sla_dict:
  if instance.getPortalType() != 'Slave Instance':
    sla_error_list.append('instance_guid is provided to a Software Instance')
  else:
    instance_guid = sla_dict.pop("instance_guid")
    software_instance = compute_partition.getAggregateRelatedValue(portal_type='Software Instance')
    if software_instance is None:
      sla_error_list.append('instance_guid provided but no Software Instance was found')

  if software_instance.getReference() != instance_guid:
    sla_error_list.append('instance_guid do not match (%s != %s)' % (
      instance_guid != software_instance.getReference()))

if 'network_guid' in sla_dict:
  network_guid = sla_dict.pop('network_guid')
  network_reference = compute_node.getSubordinationReference()
  if network_reference != network_guid:
    sla_error_list.append('network_guid do not match (%s != %s)' % (
      network_guid, network_reference))

project_reference = compute_node.getFollowUpReference()
if 'project_guid' in sla_dict:
  project_guid = sla_dict.pop("project_guid")
  if project_reference != project_guid:
    sla_error_list.append('project_guid do not match (%s != %s)' % (
      project_guid, project_reference))

instance_project_reference = instance.getFollowUpReference()
if project_reference != instance_project_reference:
  sla_error_list.append("Instance and Compute node project don't match (%s != %s)" % (
    project_reference, instance_project_reference))

return sla_error_list
