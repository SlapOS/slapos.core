import json

portal = context.getPortalObject()
active_process = portal.restrictedTraverse(active_process)

result_list = [ json.loads(result.detail.decode('zlib')) for result in active_process.getResultList() ]
result_list.sort()

data = {
  "node_id":context.getReference(),
  # Here it should not be hardcoded
  "document_hash_list": result_list,
  "timestamp": timestamp
}

portal.hash_document_record_module.newContent(
  portal_type="Hash Document Record",
  aggregate=context.getRelativeUrl(),
  title="%s-%s" % (context.getReference(), timestamp),
  text_content=json.dumps(data)
)

# delete no longer needed active process
active_process.getParentValue().manage_delObjects(ids=[active_process.getId()])
