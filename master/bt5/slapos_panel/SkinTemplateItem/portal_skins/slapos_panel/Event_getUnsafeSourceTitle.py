from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

# Allow project manager to see who is sending message for this ticket
# this helps providing better support if their are multiple project's manager handling tickets
# Customer will not see which manager replied.
if context.Base_hasSlapOSProjectUserGroup(project_relation='source_project', manager=True, agent=True) or context.Base_hasSlapOSProjectUserGroup(project_relation='destination_project', manager=True, agent=True):
  return context.getSourceTitle(checked_permission='View')
return None
