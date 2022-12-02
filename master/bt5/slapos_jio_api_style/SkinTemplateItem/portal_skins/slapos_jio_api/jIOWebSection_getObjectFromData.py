portal_type = data_dict["portal_type"]

portal = context.getPortalObject()
if portal_type == "Software Installation":
  if "compute_node_id" in data_dict and "software_release_uri" in data_dict:
    compute_node = portal.portal_catalog.getComputeNodeObject(
      data_dict["compute_node_id"],
    )
    if compute_node:
      return compute_node.getSoftwareInstallationFromUrl(data_dict["software_release_uri"])

elif portal_type == "Compute Node":
  if "compute_node_id" in data_dict:
    compute_node_id = data_dict["compute_node_id"]
    user = portal.portal_membership.getAuthenticatedMember().getUserName()
    if str(user) == compute_node_id:
      compute_node = portal.portal_membership.getAuthenticatedMember().getUserValue()
      compute_node.setAccessStatus(compute_node_id)
    else:
      compute_node = portal.portal_catalog.getComputeNodeObject(compute_node_id)
    if compute_node:
      return compute_node

elif portal_type == "Software Instance":
  if "reference" in data_dict:
    software_instance = portal.portal_catalog.getSoftwareInstanceObject(
      data_dict["reference"],
      include_shared=True
    )
    if software_instance:
      return software_instance
  elif "compute_node_id" and "compute_partition_id" in data_dict:
    compute_partition = portal.portal_catalog.getComputePartitionObject(
      data_dict["compute_node_id"],
      data_dict["compute_partition_id"],
    )
    if compute_partition:
      return compute_partition.getSoftwareInstance()

elif portal_type == "Software Instance Certificate Record":
  if "reference" in data_dict:
    software_instance = portal.portal_catalog.getSoftwareInstanceObject(
      data_dict["reference"],
      include_shared=True
    )
    if software_instance:
      return software_instance.newContent(
        temp_object=True,
        portal_type="Software Instance Certificate Record",
      )

elif portal_type == "Hash Document Record":
  if "reference" in data_dict:
    return portal.portal_catalog.getResultValue(
      portal_type="Hash Document Record",
      reference=data_dict["reference"]
    )

return None
