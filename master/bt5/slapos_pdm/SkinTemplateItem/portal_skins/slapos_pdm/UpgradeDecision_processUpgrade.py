from DateTime import DateTime

upgrade_decision = context
if upgrade_decision.getSimulationState() != 'started':
  # Update Decision is not on started state, Upgrade is not possible!
  return

instance_tree = upgrade_decision.getAggregateValue("Instance Tree")
software_release_url = upgrade_decision.getSoftwareReleaseValue().getUrlString()

status = instance_tree.getSlapState()

if status == "start_requested":
  state = "started"
elif status == "stop_requested":
  state = "stopped"
elif status == "destroy_requested":
  state = "destroyed"
else:
  raise ValueError('Unhandled state: %s' % status)

if state == 'destroyed':
  # Nothing to do
  upgrade_decision.reject(
    comment="Instance Tree destroyed")
else:
  person = instance_tree.getDestinationSectionValue(portal_type="Person")
  person.requestSoftwareInstance(
    state=state,
    software_release=software_release_url,
    software_title=instance_tree.getTitle(),
    software_type=instance_tree.getSourceReference(),
    instance_xml=instance_tree.getTextContent(),
    sla_xml=instance_tree.getSlaXml(),
    shared=instance_tree.isRootSlave(),
    project_reference=instance_tree.getFollowUpReference(),
    force_software_change=True
  )

  upgrade_decision.stop(
    comment="Upgrade Processed for the Instance Tree!")
