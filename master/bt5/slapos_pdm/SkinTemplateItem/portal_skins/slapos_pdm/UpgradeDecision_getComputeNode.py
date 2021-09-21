compute_node_list = []
for decision_line in context.contentValues():
  compute_node_list.extend(
    decision_line.getAggregateValueList(portal_type="Compute Node"))

if len(compute_node_list) > 1: 
  raise ValueError("It is only allowed to have more them 1 Compute Node")

if len(compute_node_list) == 0:
  return None


return compute_node_list[0]
