portal = context.getPortalObject()
project = context
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

workgroup = person.Person_getProjectCustomerWorkgroup(project)
if workgroup is not None:
  return workgroup.getTitle()
