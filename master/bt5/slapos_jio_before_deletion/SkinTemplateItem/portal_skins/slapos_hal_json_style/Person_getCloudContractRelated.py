portal = context.getPortalObject()
import json

contract = portal.portal_catalog.getResultValue(
  portal_type="Cloud Contract",
  default_destination_section_uid=context.getUid(),
  validation_state=['invalidated', 'validated'],
)
if contract is not None:
  if return_json:
    return json.dumps(contract.getRelativeUrl())

  return contract.getRelativeUrl()

if return_json:
  return json.dumps("")

return
