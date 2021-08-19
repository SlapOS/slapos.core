import json
request = context.REQUEST
try:
  context.generateCertificate()
  return json.dumps({
    "certificate" : request.get('compute_node_certificate'),
    "key" : request.get('compute_node_key')
  })
except ValueError:
  return json.dumps(False)
