from DateTime import DateTime
import json

memcached_dict = context.Base_getSlapToolMemcachedDict()
try:
  d = memcached_dict[context.getReference()]
except KeyError:
  return "Compute Node didn't contact the server"
else:
  log_dict = json.loads(d)
  date = DateTime(log_dict['created_at'])
  return date.strftime('%Y/%m/%d %H:%M')
