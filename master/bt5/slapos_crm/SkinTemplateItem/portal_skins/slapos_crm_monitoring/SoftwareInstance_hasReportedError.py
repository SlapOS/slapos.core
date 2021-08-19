from DateTime import DateTime
import json

if context.getAggregateValue(portal_type="Compute Partition") is not None:
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
  since = DateTime(d.get('since'))

  # Optimise by checking memcache information first.
  if result.startswith('#error '):
    if ((DateTime()-since)*24*60) > tolerance:
      if include_created_at and not include_since:
        return result, last_contact
      elif include_created_at and include_since:
        return result, last_contact, since
      return result

  # XXX time limit of 48 hours for run at least once.
  if include_message and include_created_at and not include_since:
    return result, last_contact
  elif include_message and include_created_at and include_since:
    return result, last_contact, since
  elif include_message and not include_created_at:
    return result

return None
