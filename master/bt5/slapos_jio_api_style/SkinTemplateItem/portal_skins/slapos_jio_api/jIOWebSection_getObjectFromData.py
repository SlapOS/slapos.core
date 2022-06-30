portal_type = data_dict["portal_type"]

portal = context.getPortalObject()
if portal_type == "Software Installation":
  if "compute_node_id" in data_dict and "software_release_uri" in data_dict:
    compute_node = portal.portal_catalog.getComputeNodeObject(
      data_dict["compute_node_id"],
    )
    if compute_node:
      return compute_node.getSoftwareInstallationFromUrl(data_dict["software_release_uri"])

elif portal_type == "Software Instance":
  if "reference" in data_dict:
    software_instance = portal.portal_catalog.getSoftwareInstanceObject(
      data_dict["reference"],
      include_shared=True
    )
    if software_instance:
      return software_instance

return None
