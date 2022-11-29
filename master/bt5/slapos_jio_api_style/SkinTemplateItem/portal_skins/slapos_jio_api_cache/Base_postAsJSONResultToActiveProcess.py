from Products.CMFActivity.ActiveResult import ActiveResult
import hashlib
data = {
  "timestamp": context.getSlapTimestamp(),
  "reference": context.getReference(),
  "md5sum": hashlib.md5(context.asJSONText()).hexdigest(),
  "method": "python: hashlib.md5(json_text).hexdigest()",
  "data-schema": context.getJSONSchemaUrl()
}
import json
context.getPortalObject().restrictedTraverse(active_process).postResult(
  ActiveResult(detail=json.dumps(data).encode('utf8').encode('zlib')))
