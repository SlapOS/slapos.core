portal = context.getPortalObject()

tag = "%s-%s" % (context.getReference(), script.getId())
aggregate_tag = "%s:aggregate" % tag

if portal.portal_activities.countMessageWithTag(tag) or \
      portal.portal_activities.countMessageWithTag(aggregate_tag):
  return

if context.getPortalType() == "Compute Node":
  compute_partition_list = portal.portal_catalog(
    portal_type="Compute Partition",
    validation_state="validated"
  )
  if not compute_partition_list:
    return
  compute_partition_uid_list = [x.uid for x in compute_partition_list]
  search_kw = {
    "portal_type":"Software Instance",
    "default_aggregate_uid":compute_partition_uid_list,
    "validation_state":"validated",
  }
else:
  # Case the Node is an Instance
  search_kw = {
    "default_aggregate_uid": context.getAggregateUid(),
    "portal_type": "Slave Instance",
    "validation_state": "validated",
    "slapos_item.slap_state": "start_requested",
  }

import time
now = int(time.time())
priority = 4
compute_node_active_process = portal.portal_activities.newActiveProcess()

portal.portal_catalog.searchAndActivate(
  method_id="Base_postAsJSONResultToActiveProcess",
  activate_kw=dict(tag=tag, priority=priority),
  method_kw=dict(active_process=compute_node_active_process.getRelativeUrl()),
  **search_kw
)

context.activate(
  tag=aggregate_tag,
  after_tag=tag,
  activity='SQLQueue').SlapOSNode_aggregateHashFile(
    timestamp=now,
    active_process=compute_node_active_process.getRelativeUrl()
  )
