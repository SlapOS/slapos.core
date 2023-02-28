compute_node = context.getPortalObject().portal_catalog.getResultValue(
    portal_type='Compute Node',
    # XXX Hardcoded validation state
    validation_state="validated",
    reference=data_dict["compute_node_id"],
)
if not compute_node:
  return context.ERP5Site_logApiErrorAndReturn(
    error_code="404",
    error_message="Compute Node not found",
    error_name="COMPUTE-NODE-NOT-FOUND",
  )
import urllib
compute_node.requestSoftwareRelease(
  software_release_url=urllib.unquote(data_dict["software_release_uri"]),
  state=data_dict.get("state", "available"),
)

import json
return json.dumps({
  "$schema": "id-response-schema.json",
  "id": context.REQUEST.get("software_installation_url")
}, indent=2)
