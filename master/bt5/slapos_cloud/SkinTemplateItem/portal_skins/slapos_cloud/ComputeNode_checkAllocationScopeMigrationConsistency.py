error_list = []
if context.getAllocationScope() != "open/friend" or \
    context.getPortalType() != "Compute Node":
  # Skip if the document isn't on 
  return error_list

if fixit:
  owner = context.getSourceAdministrationValue()
  if  owner is not None and \
      context.getSubjectList() == [owner.getDefaultEmailText()]:
    # The user shared his computer with himself only.
    context.setSubjectList([])
    context.setAllocationScope("open/personal")
  elif not (context.getSubjectList()):
    # The user shared his computer with himself only, so just move into
    # Personal
    context.setAllocationScope("open/personal")
  else:
    # XXX here we have to finish it up
    pass
else:
  error_list.append('Compute Node has to migrate allocation scope from friend to personal')

return error_list
