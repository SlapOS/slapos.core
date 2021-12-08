from zExceptions import Unauthorized
organisation = state_change['object']
portal = organisation.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise Unauthorized

for assignment in person.objectValues(portal_type="Assignment"):
  if assignment.getDestinationSection() == organisation.getRelativeUrl() and \
       assignment.getValidationState() != 'closed':
    assignment.close()
    break
