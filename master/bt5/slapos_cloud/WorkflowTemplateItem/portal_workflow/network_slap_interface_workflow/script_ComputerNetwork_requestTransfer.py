computer_network = state_change["object"]
from DateTime import DateTime
from zExceptions import Unauthorized

portal = computer_network.getPortalObject()

# Get required arguments
kwargs = state_change.kwargs

user = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user is None or user.getRelativeUrl() !=  computer_network.getSourceAdministration():
  raise Unauthorized("Only the Computer Network owner can transfer it from one location to another.")

# Required args
# Raise TypeError if all parameters are not provided
try:
  # destination_project=None, destination_section=None
  destination_section = kwargs['destination_section']
  destination_project = kwargs["destination_project"]
except KeyError:
  raise TypeError("ComputerNetwork_requestTransfer takes exactly 2 arguments")

tag = "%s_%s_%s_inProgress" % (computer_network.getUid(), destination_section, destination_project)
if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

movement_portal_type = "Internal Packing List"

source_project = computer_network.Item_getCurrentProjectValue()
source_section = computer_network.Item_getCurrentOwnerValue()
source = computer_network.getSourceAdministration()
destination = computer_network.getSourceAdministration()
resource_value = portal.product_module.compute_node

if destination_project is None and source_project is not None:
  destination_project = source_project.getRelativeUrl()

if source_section is None:
  source_section = computer_network.getSourceAdministrationValue()

if destination_section is None:
  destination_section = source_section.getRelativeUrl()

module = portal.getDefaultModule(portal_type=movement_portal_type)
line_portal_type = '%s Line' % movement_portal_type

delivery = module.newContent(title="Transfer %s to %s" % (computer_network.getTitle(), destination_project),
                             source=source,
                             source_section_value=source_section,
                             source_project_value=source_project,
                             destination=destination,
                             destination_section=destination_section,
                             source_decision=destination_section,
                             destination_decision=destination_section,
                             destination_project=destination_project,
                             start_date=DateTime(),
                             stop_date=DateTime(),
                             portal_type=movement_portal_type)

delivery_line = delivery.newContent(
                    portal_type=line_portal_type,
                    title=computer_network.getReference(),
                    quantity_unit=resource_value.getQuantityUnit(),
                    resource_value=resource_value)

delivery_line.edit(
              price=0.0,
              quantity=1.0,
              aggregate=computer_network.getRelativeUrl())


delivery.confirm()
delivery.stop()
delivery.deliver()

delivery.reindexObject(activate_kw=dict(tag=tag))
delivery_line.reindexObject(activate_kw=dict(tag=tag))
