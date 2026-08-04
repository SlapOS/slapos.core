person = context
workgroup = person.Person_getProjectCustomerWorkgroup(project)
if workgroup is None:
  return person
return workgroup
