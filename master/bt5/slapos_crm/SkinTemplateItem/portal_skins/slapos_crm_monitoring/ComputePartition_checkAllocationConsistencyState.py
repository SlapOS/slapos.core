portal = context.getPortalObject()
compute_partition = context
error_dict = {}

compute_node = compute_partition.getParentValue()
assert compute_node.getPortalType() in ['Compute Node', 'Remote Node']

instance_list = compute_partition.getAggregateRelatedValueList(portal_type=[
  'Software Instance', 'Slave Instance'])

for instance in instance_list:
  instance_sla_error_list = []
  if instance.getValidationState() != 'validated' or \
      instance.getSlapState() == 'destroy_requested':
    # Outdated catalog or instance under garbage collection,
    # we skip for now.
    continue

  sla_dict = instance.getSlaXmlAsDict()
  if sla_dict:
    # Simple check of instance SLAs
    if "computer_guid" in sla_dict:
      computer_guid = sla_dict.pop("computer_guid")
      if compute_node.getReference() != computer_guid:
        instance_sla_error_list.append('computer_guid do not match on: %s (%s != %s)' % (
          instance.getTitle(), computer_guid, compute_node.getReference()))

    if "instance_guid" in sla_dict:
      if instance.getPortalType() != 'Slave Instance':
        instance_sla_error_list.append('instance_guid is provided to a Software Instance: %s' % instance.getTitle())
      else:
        instance_guid = sla_dict.pop("instance_guid")
        software_instance = compute_partition.getAggregateRelatedValue(portal_type='Software Instance')
        if software_instance is None:
          instance_sla_error_list.append('instance_guid provided on %s but no Software Instance was found' % instance.getTitle())
        else:
          if software_instance.getReference() != instance_guid:
            instance_sla_error_list.append('instance_guid do not match on: %s (%s != %s)' % (
              instance.getTitle(), instance_guid, software_instance.getReference()))

    if 'network_guid' in sla_dict:
      network_guid = sla_dict.pop('network_guid')
      network_reference = compute_node.getSubordinationReference()
      if network_reference != network_guid:
        instance_sla_error_list.append('network_guid do not match on: %s (%s != %s)' % (
          instance.getTitle(), network_guid, network_reference))

    project_reference = compute_node.getFollowUpReference()
    if 'project_guid' in sla_dict:
      project_guid = sla_dict.pop("project_guid")
      if project_reference != project_guid:
        instance_sla_error_list.append('project_guid do not match on: %s (%s != %s)' % (
          instance.getTitle(), project_guid, project_reference))

    instance_project_reference = instance.getFollowUpReference()
    if project_reference != instance_project_reference:
      instance_sla_error_list.append("Instance and Compute node project don't match on: %s (%s != %s)" % (
        instance.getTitle(), project_reference, instance_project_reference))

    if instance_sla_error_list:
      error_dict[instance.getRelativeUrl()] = {
        'instance': instance,
        'sla_error_list': instance_sla_error_list
      }

  # Now check allocation supply consistency
  instance_tree = instance.getSpecialiseValue(portal_type="Instance Tree")

  # if there is an ongoing upgrade decision, skip, since there is already
  # a ticket for handle the inconsistency.
  if portal.portal_catalog.getResultValue(
    portal_type='Upgrade Decision',
    aggregate__uid=instance_tree.getUid(),
    simulation_state=['started', 'stopped', 'planned', 'confirmed']) is not None:
    continue

  instance_tree_context = instance_tree.asContext(
    default_source_reference=instance.getSourceReference(),
    url_string=instance.getUrlString())

  software_product, software_release, software_type = instance_tree_context.InstanceTree_getSoftwareProduct()
  if software_product is None:
    if instance.getRelativeUrl() not in error_dict:
      error_dict[instance.getRelativeUrl()] = {'instance': instance}
    message = 'No Software Product matching for: %s' % instance.getTitle()
    error_dict[instance.getRelativeUrl()]['allocation_supply_error'] = message
    continue

  project = instance.getFollowUpValue()
  assert project is not None, 'Project is None'

  person = instance_tree.getDestinationSectionValue()
  allocation_cell_list = project.Project_getSoftwareProductPredicateList(
    software_product=software_product,
    software_product_type=software_type,
    software_product_release=software_release,
    destination_value=person,
    node_value=compute_node,
    predicate_portal_type='Allocation Supply Cell'
  )
  if not allocation_cell_list:
    if instance.getRelativeUrl() not in error_dict:
      error_dict[instance.getRelativeUrl()] = {'instance': instance}
    message = 'No Allocation Supply for: %s' % instance.getTitle()
    error_dict[instance.getRelativeUrl()]['allocation_supply_error'] = message

return error_dict
