from zExceptions import Unauthorized
project = state_change['object']
portal = project.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise Unauthorized

if project.getDestinationDecision() == person.getRelativeUrl():
  project.setDestinationDecision(None)

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getDestinationProject() == project.getRelativeUrl() and \
       assignment.getValidationState() != 'closed':
    assignment.close()
    break
