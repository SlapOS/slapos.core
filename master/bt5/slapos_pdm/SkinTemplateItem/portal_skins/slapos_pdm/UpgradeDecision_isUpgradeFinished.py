portal = context.getPortalObject()

instance_tree = context.UpgradeDecision_getAggregateValue("Instance Tree")
compute_node = context.UpgradeDecision_getAggregateValue("Compute Node")
software_release = context.UpgradeDecision_getSoftwareRelease()

if instance_tree is not None:
  if instance_tree.getUrlString() == software_release.getUrlString():
    return True

elif compute_node is not None:
  full_software_release_list = [si for si in 
          portal.portal_catalog(
            portal_type='Software Installation',
            url_string=software_release.getUrlString(),
            default_aggregate_uid=compute_node.getUid(),
            validation_state='validated'
          ) if si.getSlapState() == 'start_requested']

  if len(full_software_release_list) > 0:
    return True

return False
