if context.getSimulationState() != 'started':
  # Update Decision is not on started state, Upgrade is not possible!
  return False

instance_tree = context.UpgradeDecision_getInstanceTree()
software_release = context.UpgradeDecision_getSoftwareRelease()

if instance_tree is None:
  return False

if software_release is None:
  return False 

software_release_url = software_release.getUrlString()
person = instance_tree.getDestinationSectionValue(portal_type="Person")

# Test if the Software is available at the Computer.
if not instance_tree.InstanceTree_isUpgradePossible(
  software_release_url=software_release_url):
  return

status = instance_tree.getSlapState()
if status == "start_requested":
  state = "started"
elif status == "stop_requested":
  state = "stopped"
elif status == "destroy_requested":
  state = "destroyed"
  
person.requestSoftwareInstance(
  state=state,
  software_release=software_release_url,
  software_title=instance_tree.getTitle(),
  software_type=instance_tree.getSourceReference(),
  instance_xml=instance_tree.getTextContent(),
  sla_xml=instance_tree.getSlaXml(),
  shared=instance_tree.isRootSlave()
)

context.stop()

return True
