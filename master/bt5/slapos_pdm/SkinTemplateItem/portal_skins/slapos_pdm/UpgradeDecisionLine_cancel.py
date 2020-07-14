hosting_subscription = context.getAggregateValue(portal_type="Hosting Subscription")

software_release = context.getAggregateValue(portal_type="Software Release")

upgrade_decision = context.getParentValue()

if software_release.getValidationState() == "archived":
  upgrade_decision.cancel(comment="Software Release is archived.")
  return

if hosting_subscription is not None:
  if hosting_subscription.getUpgradeScope() in ['never', 'disabled']:
    upgrade_decision.cancel("Upgrade scope was disabled on the related Hosting Subscription")

  if hosting_subscription.getSlapState() == "destroy_requested":
    upgrade_decision.cancel(comment="Hosting Subscription is destroyed.")

  elif hosting_subscription.getUrlString() == software_release.getUrlString():
    upgrade_decision.cancel(comment="Hosting subscription is already upgraded.")

  return

computer = context.getAggregateValue(portal_type="Computer")
if computer is not None:
  if computer.getUpgradeScope() in ['never', 'disabled']:
    upgrade_decision.cancel("Upgrade scope was disabled on the related Hosting Subscription")

  if computer.getAllocationScope() in ["closed/forever", "closed/termination"]:
    upgrade_decision.cancel(comment="Computer is closed.")
    return

  already_deployed = len(context.portal_catalog(limit=1,
    portal_type="Computer Partition",
    parent_reference=computer.getReference(),
    software_release_url=software_release.getUrlString()))
  if already_deployed:
    upgrade_decision.cancel(comment="Computer already has the software release")
