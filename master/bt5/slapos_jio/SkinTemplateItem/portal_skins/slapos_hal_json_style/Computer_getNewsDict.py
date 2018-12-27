from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

def get_computer_partition_dict(reference):
  computer_dict =  context.Base_getNewsDict(context)
  computer_partition_dict = { }
  for computer_partition in context.objectValues(portal_type="Computer Partition"):
    software_instance = computer_partition.getAggregateRelatedValue(portal_type="Software Instance")
    if software_instance is not None:
      computer_partition_dict[computer_partition.getTitle()] = context.Base_getNewsDict(software_instance)

  return {"computer": computer_dict,
          "partition": computer_partition_dict}

# Use Cache here, at least transactional one.
return get_computer_partition_dict(context.getReference())
