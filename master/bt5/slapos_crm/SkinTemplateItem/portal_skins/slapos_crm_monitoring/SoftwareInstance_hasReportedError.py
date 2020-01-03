from DateTime import DateTime
import json

if context.getAggregateValue(portal_type="Computer Partition") is not None:
  memcached_dict = context.Base_getSlapToolMemcachedDict()
  try:
    d = memcached_dict[context.getReference()]
  except KeyError:
    if include_message:
      return "Not possible to connect"
    return

  d = json.loads(d)
  result = d['text']
  last_contact = DateTime(d.get('created_at'))

  # Optimise by checking memcache information first.
  if result.startswith('#error '):
    if include_created_at:
      return result, last_contact
    return result

  # XXX time limit of 48 hours for run at least once.
  if include_message and include_created_at:
    return result, last_contact

  if include_message and not include_created_at:
    return result

return None
