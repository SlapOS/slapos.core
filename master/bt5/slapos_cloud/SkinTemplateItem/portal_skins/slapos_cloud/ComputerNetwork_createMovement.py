"""
  Create an internal Packing List and attach the computer network
"""
tag = "transfer_compute_network_%s" % context.getUid()
context.activate(activity="SQLQueue", tag=tag).requestTransfer(
  destination_project=destination_project,
  destination_section=destination_section
)
