portal = context.getPortalObject()
user = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user is None:
  return
  
portal_type = context.getPortalType()
if portal_type in ["Compute Node", "Computer Network"]:
  return user.getRelativeUrl() == context.getSourceAdministration()

if portal_type == "Instance Tree":
  return user.getRelativeUrl() == context.getDestinationSection()

raise ValueError("Unsupported Type")
