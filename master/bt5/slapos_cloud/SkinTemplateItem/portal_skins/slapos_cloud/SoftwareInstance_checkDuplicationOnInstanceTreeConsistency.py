if context.getSlapState() == "destroy_requested":
  return []

instance_tree = context.getSpecialiseValue(portal_type="Instance Tree")

error_list = []

if instance_tree:
  title = context.getTitle()
  for instance in instance_tree.getSpecialiseRelatedValueList(
                   portal_type=["Slave Instance", "Software Instance"]):
    if instance.getSlapState() == "destroy_requested" or\
               instance.getUid() == context.getUid():
      continue
      
    if instance.getTitle() == title:
      error_list.append("%s is duplicated with %s " % (
        title, instance.getRelativeUrl()))

return error_list
