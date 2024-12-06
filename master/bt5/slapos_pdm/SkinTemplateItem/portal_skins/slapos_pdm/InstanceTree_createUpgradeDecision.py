from DateTime import DateTime
portal = context.getPortalObject()
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

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

compute_node, allocation_cell_list = instance_tree.InstanceTree_getNodeAndAllocationSupplyCellList(
  software_product=software_product,
  software_release=target_software_release,
  software_type=target_software_type or software_type)

# Only upgrade if there is no doubt (ie, only 1 url is allowed)
if len(allocation_cell_list) == 1:
  if (allocation_cell_list[0].getSoftwareReleaseValue().getUrlString() != instance_tree.getUrlString()):
    # XXX Upgrade

    if compute_node is not None:
      if compute_node.getRelativeUrl() not in allocation_cell_list[0].getParentValue().getParentValue().getAggregateList():
        return

    if portal.portal_catalog.getResultValue(
      portal_type='Upgrade Decision',
      aggregate__uid=instance_tree.getUid(),
      simulation_state=['rejected'],
      software_release__uid=allocation_cell_list[0].getSoftwareReleaseUid()
    ):
      # If same upgrade decision has been rejected, do nothing
      return

    decision_title = 'A new upgrade is available for %s' % instance_tree.getTitle()
    person_relative_url = context.getDestinationSection()
    upgrade_decision = portal.upgrade_decision_module.newContent(
      portal_type='Upgrade Decision',
      title=decision_title,
      destination=person_relative_url,
      destination_section=person_relative_url,
      destination_decision=person_relative_url,
      destination_project_value=instance_tree.getFollowUpValue(),
      resource_value=software_product,
      variation_category_list=allocation_cell_list[0].getVariationCategoryList(),
      aggregate_value=instance_tree,
      # As a ticket, give the ticket original context
      causality_value=instance_tree,
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
