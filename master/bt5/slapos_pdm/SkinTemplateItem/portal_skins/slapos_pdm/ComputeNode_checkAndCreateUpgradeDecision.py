from DateTime import DateTime
compute_node = context
portal = context.getPortalObject()

upgrade_scope = context.getUpgradeScope()
if upgrade_scope in ["never", "disabled"]:
  return

full_software_release_list = [si.url_string for si in
              portal.portal_catalog(
                select_dict = {"url_string": None},
                portal_type='Software Installation',
                default_aggregate_uid=compute_node.getUid(),
                validation_state='validated'
              ) if si.getSlapState() == 'start_requested']

if len(full_software_release_list) == 0:
  return
# group SR by Software Product to avoid two upgrade Decision for the same product
software_release_list = portal.portal_catalog(
                          portal_type='Software Release',
                          url_string=full_software_release_list,
                          group_by=['default_aggregate_uid']
                        )
upgrade_decision_list = []
for software_release in software_release_list:
  software_product_reference = software_release.getAggregateReference()
  if software_product_reference in [None, ""]:
    continue

  sorted_list = portal.SoftwareProduct_getSortedSoftwareReleaseList(
    software_product_reference=software_product_reference)

  # Check if there is a new version of this software Product
  if sorted_list and \
      sorted_list[0].getUrlString() not in full_software_release_list:

    newer_release = sorted_list[0]
    title = 'A new version of %s is available for %s' % \
                        (software_product_reference, context.getTitle())
    # If exist upgrade decision in progress try to cancel it
    decision_in_progress = newer_release.\
            SoftwareRelease_getUpgradeDecisionInProgress(compute_node.getUid())
    if decision_in_progress:
      decision_in_progress.reviewRegistration(
        software_release_url=newer_release.getUrlString())
      if decision_in_progress.getSimulationState() != "cancelled":
        continue

    upgrade_decision = newer_release.SoftwareRelease_createUpgradeDecision(
        source_url=compute_node.getRelativeUrl(),
        title=title)

    upgrade_decision.approveRegistration(
      upgrade_scope=compute_node.getUpgradeScope("ask_confirmation"))
    upgrade_decision_list.append(upgrade_decision)

return upgrade_decision_list