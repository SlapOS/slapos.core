person = state_change['object']
portal = person.getPortalObject()
# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  computer_network_title = kwargs['network_title']
except KeyError:
  raise TypeError("Person_requestNetwork takes exactly 1 argument")

tag = "%s_%s_NetworkInProgress" % (person.getUid(), 
                               computer_network_title)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

computer_network_portal_type = "Computer Network"
computer_network_list = portal.portal_catalog.portal_catalog(
  portal_type=computer_network_portal_type,
  title=computer_network_title,
  validation_state="validated",
  limit=2)

if len(computer_network_list) == 2:
  raise NotImplementedError
elif len(computer_network_list) == 1:
  context.REQUEST.set("computer_network_relative_url", computer_network_list[0].getRelativeUrl())
  context.REQUEST.set("computer_network_reference", computer_network_list[0].getReference())
else:
  module = portal.getDefaultModule(portal_type=computer_network_portal_type)
  computer_network = module.newContent(
    portal_type=computer_network_portal_type,
    title=computer_network_title,
    source_administration=person.getRelativeUrl(),
    activate_kw={'tag': tag}
  )
  context.REQUEST.set("computer_network_relative_url", computer_network.getRelativeUrl())
  context.REQUEST.set("computer_network_reference", computer_network.getReference())

  computer_network.approveRegistration()
