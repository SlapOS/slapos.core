from DateTime import DateTime
portal = context.getPortalObject()

instance_tree = context
upgrade_scope = context.getUpgradeScope("ask_confirmation")
if upgrade_scope in ["never", "disabled"]:
  return

root_instance_list = [
  q for q in instance_tree.getSuccessorValueList(portal_type=["Software Instance", "Slave Instance"])
  if q.getSlapState() != 'destroy_requested']
if len(root_instance_list) == 0:
  return
root_instance = root_instance_list[0]

slave_upgrade = False
if root_instance.getPortalType() == 'Slave Instance':
  slave_upgrade = True
  upgrade_scope = "auto"

if instance_tree.getSlapState() == "destroy_requested":
  return

tag = "%s_requestUpgradeDecisionCreation_inProgress" % instance_tree.getUid()
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return

partition = root_instance.getAggregateValue(portal_type="Compute Partition")
if partition is None:
  return

decision_title = 'A new upgrade is available for %s' % instance_tree.getTitle()
newer_release = None

if slave_upgrade:
  software_instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
  if software_instance:
    url_string = software_instance.getUrlString()
    if url_string != instance_tree.getUrlString():
      newer_release = context.portal_catalog.getResultValue(portal_type='Software Release', url_string=url_string)
else:
  if not partition.getParentValue().getAllocationScopeUid() in [category.getUid() \
      for category in portal.portal_categories.allocation_scope.open.objectValues()]:
    return
  newer_release = instance_tree.\
                  InstanceTree_getUpgradableSoftwareRelease()
if newer_release is None:
  return

decision_in_progress = newer_release.\
    SoftwareRelease_getUpgradeDecisionInProgress(instance_tree.getUid())

if decision_in_progress:
  decision_in_progress.reviewRegistration(
    software_release_url=newer_release.getUrlString())
  if decision_in_progress.getSimulationState() != "cancelled":
    return

upgrade_decision = newer_release.SoftwareRelease_createUpgradeDecision(
  source_url=instance_tree.getRelativeUrl(),
  title=decision_title
)

upgrade_decision.approveRegistration(
  upgrade_scope=upgrade_scope)

return upgrade_decision
