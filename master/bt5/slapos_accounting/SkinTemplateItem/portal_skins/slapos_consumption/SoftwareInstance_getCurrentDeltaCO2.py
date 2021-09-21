from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

compute_partition_list = context.getAggregateValueList(portal_type="Compute Partition")

current_watt = context.SoftwareRelease_getDeltaCO2List(
  compute_partition_list, context.SoftwareInstance_getAverageCPULoad()
)

return current_watt.keys()[0]
