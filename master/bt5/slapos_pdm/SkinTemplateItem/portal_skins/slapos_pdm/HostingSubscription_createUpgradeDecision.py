from DateTime import DateTime
portal = context.getPortalObject()

hosting_subscription = context
upgrade_scope = context.getUpgradeScope()
if upgrade_scope in ["never", "disabled"]:
  return

root_instance_list = [
  q for q in hosting_subscription.getPredecessorValueList(portal_type=["Software Instance", "Slave Instance"])
  if q.getSlapState() != 'destroy_requested']
if len(root_instance_list) == 0:
  return
root_instance = root_instance_list[0]

slave_upgrade = False
if root_instance.getPortalType() == 'Slave Instance':
  slave_upgrade = True
  upgrade_scope = "auto"

if hosting_subscription.getSlapState() == "destroy_requested":
  return

tag = "%s_requestUpgradeDecisionCreation_inProgress" % hosting_subscription.getUid()
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return

partition = root_instance.getAggregateValue(portal_type="Computer Partition")
if partition is None:
  return

decision_title = 'A new upgrade is available for %s' % hosting_subscription.getTitle()
newer_release = None

if slave_upgrade:
  software_instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
  if software_instance:
    url_string = software_instance.getUrlString()
    if url_string != hosting_subscription.getUrlString():
      newer_release = context.portal_catalog.getResultValue(portal_type='Software Release', url_string=url_string)
else:
  if not partition.getParentValue().getAllocationScopeUid() in [category.getUid() \
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
  title=decision_title
)
with upgrade_decision.defaultActivateParameterDict(activate_kw):
  upgrade_decision.plan()
  upgrade_decision.setStartDate(DateTime())
  if upgrade_scope == "auto":
    upgrade_decision.start()

# Prevent concurrent transaction to create 2 upgrade decision for the same hosting_subscription
hosting_subscription.serialize()

return upgrade_decision
