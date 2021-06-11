instance_tree_list = []
for decision_line in context.contentValues():
  instance_tree_list.extend(
    decision_line.getAggregateValueList(portal_type="Instance Tree"))

if len(instance_tree_list) > 1: 
  raise ValueError("It is only allowed to have more them 1 Instance Tree")

if len(instance_tree_list) == 0:
  return None


return instance_tree_list[0]
