from DateTime import DateTime
portal = context.getPortalObject()

instance_tree = context

if instance_tree.getSlapState() == "destroy_requested":
  return

if (target_software_release is not None) or (target_software_type is not None):
  # Those parameters will be use to force an upgrade decision
  # to a specific release / type
  # used by Remote Node for example
  assert target_software_release is not None
  assert target_software_type is not None

if portal.portal_catalog.getResultValue(
  portal_type='Upgrade Decision',
  aggregate__uid=instance_tree.getUid(),
  simulation_state=['started', 'stopped', 'planned', 'confirmed']
) is not None:
  # There is already a upgrade decision, do nothing
  return

# Check if UpgradeDecision_approveRegistration is running
# XXX we should instead look at the current upgrade decision state
tag = "%s_requestUpgradeDecisionCreation_inProgress" % instance_tree.getUid()
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # previous run not finished, skip
  return

software_product, software_release, software_type = instance_tree.InstanceTree_getSoftwareProduct()
if software_product is None:
  # No way to upgrade, if we can find which Software Product to upgrade
  return
assert software_release.getUrlString() == instance_tree.getUrlString()

compute_node = None
root_instance = None
root_instance_list = [
  q for q in instance_tree.getSuccessorValueList(portal_type=["Software Instance", "Slave Instance"])
  if q.getSlapState() != 'destroy_requested']
if len(root_instance_list) != 0:
  root_instance = root_instance_list[0]
  partition = root_instance.getAggregateValue()
  if partition is not None:
    compute_node = partition.getParentValue()

    if (root_instance.getPortalType() == 'Slave Instance'):
      if (compute_node.getPortalType() == 'Compute Node'):
        # Search the instance node linked to this partition
        soft_instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
        if soft_instance is None:
          return
        instance_node = soft_instance.getSpecialiseRelatedValue(portal_type='Instance Node')
        if instance_node is None:
          return
        compute_node = instance_node
      elif (compute_node.getPortalType() != 'Remote Node'):
        return

person = context.getDestinationSectionValue()
if person is None:
  return

# Search if the product with the same type
# XXX search only for the main node
allocation_cell_list = software_product.getFollowUpValue().Project_getSoftwareProductPredicateList(
  software_product=software_product,
  software_product_type=target_software_type or software_type,
  software_product_release=target_software_release,
  destination_value=person,
  node_value=compute_node,
  predicate_portal_type='Allocation Supply Cell'
)

if (compute_node is None) and (root_instance is not None):
  # Do not upgrade if there is no instance yet
  allocation_cell_node_list = [(x, [y.getPortalType() for y in x.getParentValue().getParentValue().getAggregateValueList()]) for x in allocation_cell_list]
  if (root_instance.getPortalType() == 'Slave Instance'):
    allocation_cell_list = [x for x, y in allocation_cell_node_list if ("Remote Node" in y) or ("Instance Node" in y)]
  elif (root_instance.getPortalType() == 'Software Instance'):
    allocation_cell_list = [x for x, y in allocation_cell_node_list if ("Remote Node" in y) or ("Compute Node" in y)]

# Only upgrade if there is no doubt (ie, only 1 url is allowed)
if len(allocation_cell_list) == 1:
  if (allocation_cell_list[0].getSoftwareReleaseValue().getUrlString() != instance_tree.getUrlString()):
    # XXX Upgrade

    if compute_node is not None:
      assert compute_node.getRelativeUrl() in allocation_cell_list[0].getParentValue().getParentValue().getAggregateList()

    if portal.portal_catalog.getResultValue(
      portal_type='Upgrade Decision',
      aggregate__uid=instance_tree.getUid(),
      simulation_state=['rejected'],
      software_release__uid=allocation_cell_list[0].getSoftwareReleaseUid()
    ):
      # If same upgrade decision has been rejected, do nothing
      return

    decision_title = 'A new upgrade is available for %s' % instance_tree.getTitle()
    upgrade_decision = portal.upgrade_decision_module.newContent(
      portal_type='Upgrade Decision',
      title=decision_title,
      destination_section_value=person,
      destination_decision_value=person,
      destination_project_value=instance_tree.getFollowUpValue(),
      resource_value=software_product,
      variation_category_list=allocation_cell_list[0].getVariationCategoryList(),
      aggregate_value=instance_tree,
    )

    with upgrade_decision.defaultActivateParameterDict({'tag': tag}):
      if upgrade_decision.getSimulationState() == "draft":
        upgrade_decision.plan()
      upgrade_decision.setStartDate(DateTime())
      if upgrade_decision.getSimulationState() == "planned":
        upgrade_decision.confirm()

    # Prevent concurrent transaction to create 2 upgrade decision for the same instance_tree
    instance_tree.serialize()

    return upgrade_decision
