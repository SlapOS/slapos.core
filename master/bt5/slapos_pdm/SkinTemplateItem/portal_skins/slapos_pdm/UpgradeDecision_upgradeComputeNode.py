if context.getSimulationState() != 'started':
  # Update Decision is not on started state, Upgrade is not possible!
  return False

compute_node = context.UpgradeDecision_getComputeNode()
software_release = context.UpgradeDecision_getSoftwareRelease()

if compute_node is None:
  return False

if software_release is None:
  return False 

software_release_url = software_release.getUrlString()

compute_node.requestSoftwareRelease(
   software_release_url=software_release_url,
   state="available")

context.stop()

return True
