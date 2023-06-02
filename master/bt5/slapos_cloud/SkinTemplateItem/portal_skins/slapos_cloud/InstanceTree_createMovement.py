"""
  Create an internal Packing List and attach the compute_node
"""
tag = "transfer_instance_tree_%s" % context.getUid()
context.activate(activity="SQLQueue",tag=tag).requestTransfer(
  destination=destination,
  destination_project=destination_project
)
