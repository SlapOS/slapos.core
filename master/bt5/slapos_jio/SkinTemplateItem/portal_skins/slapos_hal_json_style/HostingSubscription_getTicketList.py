"""
  This script return the list of tickets related to an hosting subscription
  Ticket portal types collected here are: "Support Request", "Upgrade Decision"

  Hosting subscription is linked via 'aggregate' to then Upgrade Decision Line, so
  we need to query "Upgrade Decision Line" then get his parent which is UD.
"""

result_list = []
sort_key = ""
simulation_state_list = ["validated", "suspended", "confirmed", "started", "stopped"]
for value in context.getAggregateRelatedValueList(portal_type=["Support Request", "Upgrade Decision Line"]):
  if value.getPortalType() == "Upgrade Decision Line":
    result = value.getParent()
  else:
    result = value
  if result.getSimulationState()  in simulation_state_list:
    result_list.append(result)

def sortkey(ticket):
  if not sort_key:
    return ""
  attribute_key = "get%s" % ''.join([x.capitalize() for x in sort_key.split('_')])
  return getattr(ticket, attribute_key)()

sort_list = kwargs.get("sort_on", None)
if sort_list and len(sort_list) > 0:
  sort_key = sort_list[0][0]
  if sort_list[0][1] == "ASC":
    result_list = sorted(result_list, key=sortkey)
  else:
    result_list = sorted(result_list, key=sortkey, reverse=True)

limit_list = kwargs.get("limit", None)
if limit_list and len(limit_list) > 0:
  offset, count = (int(limit_list[0]), int(limit_list[1]))
  result_list = result_list[offset:(count + offset)]

return result_list
