"""
  Create an internal Packing List and attach the compute_node
"""
tag = "transfer_compute_node_%s" % context.getUid()
context.activate(activity="SQLQueue", tag=tag).requestTransfer(
  destination=destination,
  destination_project=destination_project,
  destination_section=destination_section
)
