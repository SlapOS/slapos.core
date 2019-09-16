from DateTime import DateTime
import json

partition = context
memcached_dict = context.Base_getSlapToolMemcachedDict()

result = ""
date = None

for si in partition.getAggregateRelatedValueList(portal_type=["Software Instance", "Slave Instance"]):
  obj = si.getObject()  

  if obj.getValidationState() != "validated":
    continue
  if obj.getSlapState() == "destroy_requested":
    continue

  try:
    d = memcached_dict[obj.getReference()]
  except KeyError:
    result = "#missing no data found for %s" % obj.getReference()
  else:
    d = json.loads(d)
    date = DateTime(d['created_at'])
    result = date.strftime('%Y/%m/%d %H:%M')

return result
