portal = context.getPortalObject()

tag = "%s-%s" % (context.getReference(), script.getId())
aggregate_tag = "%s:aggregate" % tag

if portal.portal_activities.countMessageWithTag(tag) or \
      portal.portal_activities.countMessageWithTag(aggregate_tag):
  return

compute_partition_list = portal.portal_catalog(
  portal_type="Compute Partition",
  validation_state="validated"
)
if not compute_partition_list:
  return

compute_partition_uid_list = [x.uid for x in compute_partition_list]

import time
now = int(time.time())
priority = 4
compute_node_active_process = portal.portal_activities.newActiveProcess()

portal.portal_catalog.searchAndActivate(
  method_id="Base_postAsJSONResultToActiveProcess",
  activate_kw=dict(tag=tag, priority=priority),
  method_kw=dict(active_process=compute_node_active_process.getRelativeUrl()),
  portal_type="Software Instance",
  default_aggregate_uid=compute_partition_uid_list,
  validation_state="validated",
)

portal.portal_catalog.searchAndActivate(
  method_id="Base_postAsJSONResultToActiveProcess",
  activate_kw=dict(tag=tag, priority=priority),
  method_kw=dict(active_process=compute_node_active_process.getRelativeUrl()),
  default_aggregate_uid=compute_partition_uid_list,
  portal_type="Slave Instance",
  validation_state="validated",
  **{"slapos_item.slap_state": "start_requested"}
)

context.activate(
  tag=aggregate_tag,
  after_tag=tag,
  activity='SQLQueue').ComputeNode_aggregateHashFile(
    timestamp=now,
    active_process=compute_node_active_process.getRelativeUrl()
  )
