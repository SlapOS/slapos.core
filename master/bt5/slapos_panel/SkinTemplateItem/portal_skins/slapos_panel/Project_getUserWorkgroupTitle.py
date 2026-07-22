project = context

workgroup = project.Project_getUserWorkgroup()
if workgroup is not None:
  return workgroup.getTitle()
