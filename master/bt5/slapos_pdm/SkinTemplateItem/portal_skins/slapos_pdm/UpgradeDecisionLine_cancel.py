instance_tree = context.getAggregateValue(portal_type="Instance Tree")

software_release = context.getAggregateValue(portal_type="Software Release")

upgrade_decision = context.getParentValue()

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

computer = context.getAggregateValue(portal_type="Computer")
if computer is not None:
  if computer.getUpgradeScope() in ['never', 'disabled']:
    upgrade_decision.cancel("Upgrade scope was disabled on the related Instance Tree")
    return

  elif computer.getAllocationScope() in ["closed/forever", "closed/termination"]:
    upgrade_decision.cancel(comment="Computer is closed.")
    return

  already_deployed = len(context.portal_catalog(limit=1,
    portal_type="Computer Partition",
    parent_reference=computer.getReference(),
    software_release_url=software_release.getUrlString()))
  if already_deployed:
    upgrade_decision.cancel(comment="Computer already has the software release")
