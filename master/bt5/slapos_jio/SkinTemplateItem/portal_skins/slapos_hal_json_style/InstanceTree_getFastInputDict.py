# Recommendation, keep as simple as possible.

# Use string in url because there are multiple products for ORS,
# and it would be a costly query and require Manager Proxy role.
if context.getRootSlave():
  return {}

for sr_string in ['software/re6stnet/', 'software/rapid-cdn/']:
  if context.getSuccessorReference() is not None and sr_string in context.getUrlString(''):
    return {
      'enabled': True,
      'sla_xml': '<parameter id="instance_guid">%s</parameter>' % context.getSuccessorReference()
    }

return {}
