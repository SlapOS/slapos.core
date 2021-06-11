from DateTime import DateTime
portal = context.getPortalObject()

instance_tree = context
upgrade_scope = context.getUpgradeScope()
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
activate_kw = {'tag': tag}
if portal.portal_activities.countMessageWithTag(tag) > 0:
  # nothing to do
  return

partition = root_instance.getAggregateValue(portal_type="Computer Partition")
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

if decision_in_progress and \
    not decision_in_progress.UpgradeDecision_tryToCancel(
      newer_release.getUrlString()):
  return

upgrade_decision = newer_release.SoftwareRelease_createUpgradeDecision(
  source_url=instance_tree.getRelativeUrl(),
  title=decision_title
)
with upgrade_decision.defaultActivateParameterDict(activate_kw):
  upgrade_decision.plan()
  upgrade_decision.setStartDate(DateTime())
  if upgrade_scope == "auto":
    upgrade_decision.start()

# Prevent concurrent transaction to create 2 upgrade decision for the same instance_tree
instance_tree.serialize()

return upgrade_decision
