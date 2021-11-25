from zExceptions import Unauthorized

project = state_change['object']
portal = person.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise Unauthorized

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getDestinationProject() == context.getRelativeUrl():
    assignment.close()
    break
