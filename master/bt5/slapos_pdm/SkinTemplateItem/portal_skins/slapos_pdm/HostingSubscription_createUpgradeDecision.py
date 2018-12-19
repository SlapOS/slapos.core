from DateTime import DateTime
portal = context.getPortalObject()

hosting_subscription = context
root_instance = hosting_subscription.getPredecessorValue()
if root_instance is None or root_instance.getPortalType() == "Slave Instance":
  return
if hosting_subscription.getSlapState() == "destroy_requested":
  return
partition = root_instance.getAggregateValue(portal_type="Computer Partition")
if partition is None:
  return

if not partition.getParent().getAllocationScopeUid() in [category.getUid() \
    for category in portal.portal_categories.allocation_scope.open.objectValues()]:
  return

newer_release = hosting_subscription.\
                  HostingSubscription_getUpgradableSoftwareRelease()
if newer_release is None:
  return

decision_in_progress = newer_release.\
    SoftwareRelease_getUpgradeDecisionInProgress(hosting_subscription.getUid())

if decision_in_progress and \
    not decision_in_progress.UpgradeDecision_tryToCancel(
      newer_release.getUrlString()):
  return

upgrade_decision = newer_release.SoftwareRelease_createUpgradeDecision(
  source_url=hosting_subscription.getRelativeUrl(),
  title='A new upgrade is available for %s' % hosting_subscription.getTitle()
)
upgrade_decision.plan()
upgrade_decision.setStartDate(DateTime())

return upgrade_decision
