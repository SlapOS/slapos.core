import json

portal = context.getPortalObject()
active_process = portal.restrictedTraverse(active_process)

result_list = [ json.loads(result.detail.decode('zlib')) for result in active_process.getResultList() ]
result_list.sort()

portal_type_path = portal.portal_types.restrictedTraverse("Hash Document Record")
base_url = portal.portal_preferences.getPreferredSlaposWebSiteUrl().strip("/")

reference = "%s-%s" % (context.getReference(), timestamp)

data = {
  "$schema":  "/".join([base_url, portal_type_path.getRelativeUrl(), "getTextContent"]),
  "portal_type": "",
  "reference": reference,
  "node_id":context.getReference(),
  # Here it should not be hardcoded
  "document_hash_list": result_list,
  "timestamp": timestamp
}

portal.hash_document_record_module.newContent(
  portal_type="Hash Document Record",
  aggregate=context.getRelativeUrl(),
  title=reference,
  reference=reference,
  text_content=json.dumps(data)
)

# delete no longer needed active process
active_process.getParentValue().manage_delObjects(ids=[active_process.getId()])
