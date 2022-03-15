upgrade_decision = state_change["object"]
from DateTime import DateTime

if upgrade_decision.getSimulationState() != 'started':
  # Update Decision is not on started state, Upgrade is not possible!
  return

instance_tree = upgrade_decision.UpgradeDecision_getAggregateValue("Instance Tree")
software_release = upgrade_decision.UpgradeDecision_getAggregateValue("Software Release")
compute_node = upgrade_decision.UpgradeDecision_getAggregateValue("Compute Node")

if software_release is None:
  return 

if compute_node is None and instance_tree is None:
  return

if compute_node is not None and instance_tree is not None:
  raise ValueError("Something is wrong, you cannot upgrade Compute Node and Instance Tree on the same decision.")

software_release_url = software_release.getUrlString()

if compute_node is not None:
  compute_node.requestSoftwareRelease(
   software_release_url=software_release_url,
   state="available")

  upgrade_decision.stop(comment="Upgrade Processed for the Compute Node!")
  return

# Test if the Software is available at the ComputeNode.
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

person = instance_tree.getDestinationSectionValue(portal_type="Person")
person.requestSoftwareInstance(
  state=state,
  software_release=software_release_url,
  software_title=instance_tree.getTitle(),
  software_type=instance_tree.getSourceReference(),
  instance_xml=instance_tree.getTextContent(),
  sla_xml=instance_tree.getSlaXml(),
  shared=instance_tree.isRootSlave()
)

upgrade_decision.stop(
  comment="Upgrade Processed for the Instance Tree!")
