portal_type = data_dict["portal_type"]

portal = context.getPortalObject()
if portal_type == "Software Installation":
  if "compute_node_id" in data_dict and "software_release_uri" in data_dict:
    compute_node = portal.portal_catalog.getComputeNodeObject(
      data_dict["compute_node_id"],
    )
    if compute_node:
      return compute_node.getSoftwareInstallationFromUrl(data_dict["software_release_uri"])

return None
