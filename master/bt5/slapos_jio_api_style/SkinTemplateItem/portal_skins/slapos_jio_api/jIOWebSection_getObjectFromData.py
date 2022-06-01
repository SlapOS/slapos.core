portal_type = data_dict["portal_type"]

portal = context.getPortalObject()
### Start of Duplicated code for getting documents the SlapOS way"
from Products.ERP5Type.Cache import CachingMethod

def _getNonCachedComputeNodeDocumentUrl(compute_node_reference):
  return context.Base_getUnrestrictedDocumentUrl(
      portal_type='Compute Node',
      # XXX Hardcoded validation state
      validation_state="validated",
      reference=compute_node_reference)

def _getComputeNodeDocument(compute_node_reference):
  """
  Get the validated compute_node with this reference.
  """
  result = CachingMethod(_getNonCachedComputeNodeDocumentUrl,
      id='_getComputeNodeDocument',
      cache_factory='slap_cache_factory')(compute_node_reference)
  if result:
    return portal.restrictedTraverse(result)
  return None


if portal_type == "Software Installation":
  if "compute_node_id" in data_dict and "software_release_uri" in data_dict:
    compute_node = _getComputeNodeDocument(data_dict["compute_node_id"])
    if compute_node:
      return compute_node.getSoftwareInstallationFromUrl(data_dict["software_release_uri"])

return None
