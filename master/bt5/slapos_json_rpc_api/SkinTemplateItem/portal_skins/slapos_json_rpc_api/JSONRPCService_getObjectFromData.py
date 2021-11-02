from erp5.component.document.JsonRpcAPIService import JsonRpcAPIError
portal = context.getPortalObject()

class SoftwareInstanceNotFoundError(JsonRpcAPIError):
  type = "SOFTWARE-INSTANCE-NOT-FOUND"
  status = 403

class SoftwareInstallationNotFoundError(JsonRpcAPIError):
  type = "SOFTWARE-INSTALLATION-NOT-FOUND"
  status = 403

def getSoftwareInstance(reference, include_shared=False):
  # No need to get all results if an error is raised when at least 2 objects
  # are found
  if include_shared:
    portal_type = ("Software Instance", "Slave Instance")
  else:
    portal_type = "Software Instance"
  # XXX TODO slap_tool use unrestrictedTraverse to script the security params for performance
  software_instance_list = portal.portal_catalog(
    limit=2,
    portal_type=portal_type,
    validation_state="validated",
    reference=reference
  )
  if len(software_instance_list) != 1:
    raise SoftwareInstanceNotFoundError("No instance found with reference: %s" % reference)
  return software_instance_list[0].getObject()

portal_type = data_dict["portal_type"]

if portal_type == "Software Installation":
  if "computer_guid" in data_dict and "software_release_uri" in data_dict:
    compute_node = portal.portal_catalog.getComputeNodeObject(
      data_dict["computer_guid"],
    )
    if compute_node:
      # XXX TODO slap_tool use unrestrictedTraverse to script the security params for performance
      software_installation_list = portal.portal_catalog(
        portal_type='Software Installation',
        default_aggregate_uid=compute_node.getUid(),
        validation_state='validated',
        limit=2,
        url_string={'query': data_dict["software_release_uri"], 'key': 'ExactMatch'},
      )
      if len(software_installation_list) != 1:
        raise SoftwareInstallationNotFoundError("No installation found with url: %s" % data_dict["software_release_uri"])
      return software_installation_list[0].getObject()

elif portal_type == "Compute Node":

  class ComputeNodeNotFoundError(JsonRpcAPIError):
    type = "COMPUTE-NODE-NOT-FOUND"
    status = 403

  if "computer_guid" in data_dict:
    compute_node_id = data_dict["computer_guid"]
    user = portal.portal_membership.getAuthenticatedMember().getUserName()
    if str(user) == compute_node_id:
      compute_node = portal.portal_membership.getAuthenticatedMember().getUserValue()
      compute_node.setAccessStatus(compute_node_id)
    else:
      compute_node = portal.portal_catalog.getComputeNodeObject(compute_node_id)
    if compute_node:
      return compute_node
    raise ComputeNodeNotFoundError("Compute Node '%s' not found" % data_dict["computer_guid"])

elif portal_type in ("Software Instance", "Slave Instance"):
  if "instance_guid" in data_dict:
    return getSoftwareInstance(
      data_dict["instance_guid"],
      include_shared=True
    )
  elif "computer_guid" and "compute_partition_id" in data_dict:
    compute_partition = portal.portal_catalog.getComputePartitionObject(
      data_dict["computer_guid"],
      data_dict["compute_partition_id"],
    )
    if compute_partition:
      requester_list = portal.portal_catalog(limit=2, **{
        'validation_state': 'validated',
        'portal_type': 'Software Instance',
        'aggregate__uid': compute_partition.getUid(),
      })
      if len(requester_list) != 1:
        raise SoftwareInstanceNotFoundError("No instance found with compute_node_id: %s and compute_partition_id: %s" % (data_dict["computer_guid"], data_dict["compute_partition_id"]))
      return requester_list[0].getObject()


elif portal_type == "Software Instance Certificate Record":
  if "instance_guid" in data_dict:
    return getSoftwareInstance(
      data_dict["instance_guid"],
      include_shared=True
    )

class ObjectNotFoundError(JsonRpcAPIError):
  type = "OBJECT-NODE-NOT-FOUND"
  status = 403
raise ObjectNotFoundError("Object not found")
