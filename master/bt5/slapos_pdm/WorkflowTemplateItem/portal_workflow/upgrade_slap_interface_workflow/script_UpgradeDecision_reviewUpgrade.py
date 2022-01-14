upgrade_decision = state_change["object"]
from DateTime import DateTime

portal = upgrade_decision.getPortalObject()

instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
software_release = upgrade_decision.UpgradeDecision_getAggregateValue("Software Release")

if upgrade_decision.getSimulationState() == "cancelled":
  return

if software_release.getValidationState() == "archived":
  upgrade_decision.cancel(comment="Software Release is archived.")
  return

if instance_tree is not None:
  if instance_tree.getUpgradeScope() in ['never', 'disabled']:
    upgrade_decision.cancel("Upgrade scope was disabled on the related Instance Tree")

  elif instance_tree.getSlapState() == "destroy_requested":
    upgrade_decision.cancel(comment="Instance Tree is destroyed.")

  elif instance_tree.getUrlString() == software_release.getUrlString():
    upgrade_decision.cancel(comment="Instance tree is already upgraded.")

  return

compute_node = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")
if compute_node is not None:
  if compute_node.getUpgradeScope() in ['never', 'disabled']:
    upgrade_decision.cancel("Upgrade scope was disabled on the related Instance Tree")
    return

  elif compute_node.getAllocationScope() in ["closed/forever", "closed/termination"]:
    upgrade_decision.cancel(comment="Compute Node is closed.")
    return

  already_deployed = len(portal.portal_catalog(limit=1,
    portal_type="Compute Partition",
    parent_reference=compute_node.getReference(),
    software_release_url=software_release.getUrlString()))
  if already_deployed:
    upgrade_decision.cancel(comment="Compute Node already has the software release")
