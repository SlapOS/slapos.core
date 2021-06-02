predecessor_list = context.getPredecessorList()
successor_list = context.getSuccessorList()

error_list = []

if predecessor_list:
  if successor_list:
    return ['Error: Instance has both predecessor and successor categories']

  error_list.append('Instance has predecessor categories not yet migrated to successor categories')
  if fixit:
    context.edit(successor_list=predecessor_list, predecessor_list=[])
    assert not context.getPredecessorList()
    assert len(context.getSuccessorList()) == len(predecessor_list)

return error_list
