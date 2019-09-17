from DateTime import DateTime
import json

memcached_dict = context.Base_getSlapToolMemcachedDict()
try:
  d = memcached_dict[context.getReference()]
except KeyError:
  # Information not available
  return None

d = json.loads(d)
result = d['text']
last_contact = DateTime(d.get('created_at'))

# Optimise by checking memcache information first.
if result.startswith('#error '):
  return last_contact

return None
