from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

computer_dict = {}
computer_partition_dict = {}
for computer in computer_list:
  news_dict = computer.Computer_getNewsDict()
  computer_dict[computer.getReference()] = news_dict["computer"]
  computer_partition_dict[computer.getReference()] = news_dict["partition"]

return {"computer": computer_dict,
        "partition": computer_partition_dict}
