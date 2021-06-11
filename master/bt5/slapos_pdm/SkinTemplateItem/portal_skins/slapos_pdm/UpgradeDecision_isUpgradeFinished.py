portal = context.getPortalObject()

instance_tree = context.UpgradeDecision_getInstanceTree()
computer = context.UpgradeDecision_getComputer()
software_release = context.UpgradeDecision_getSoftwareRelease()

if instance_tree is not None:
  if instance_tree.getUrlString() == software_release.getUrlString():
    return True

elif computer is not None:
  full_software_release_list = [si for si in 
          portal.portal_catalog(
            portal_type='Software Installation',
            url_string=software_release.getUrlString(),
            default_aggregate_uid=computer.getUid(),
            validation_state='validated'
          ) if si.getSlapState() == 'start_requested']

  if len(full_software_release_list) > 0:
    return True

return False
