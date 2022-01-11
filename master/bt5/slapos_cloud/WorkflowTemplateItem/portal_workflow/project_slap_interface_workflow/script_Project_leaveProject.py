from zExceptions import Unauthorized
project = state_change['object']
portal = project.getPortalObject()
person = portal.portal_membership.getAuthenticatedMember().getUserValue()

if person is None:
  raise Unauthorized

for assignment in person.objectValues(portal_type="Assignment"):
  # Close all user assignments (customer/admin/...) related to this project
  if assignment.getDestinationProject() == project.getRelativeUrl() and \
       assignment.getValidationState() != 'closed':
    assignment.close()
