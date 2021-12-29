compute_node = state_change['object']
portal = compute_node.getPortalObject()
from zExceptions import Unauthorized
from DateTime import DateTime

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  # destination=None, destination_project=None, destination_section=None
  destination = kwargs['destination']
  destination_project = kwargs["destination_project"]
  destination_section = kwargs["destination_section"]
except KeyError:
  raise TypeError("ComputeNode_requestTransfer takes exactly 3 arguments")

user = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user is None or user.getRelativeUrl() != compute_node.getSourceAdministration():
  raise Unauthorized("Only the compute_node owner can Transfer compute_node from one location to another.")

tag = "%s_%s_%s_%s_inProgress" % (compute_node.getUid(), destination, destination_project, destination_section)

if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

movement_portal_type = "Internal Packing List"

source = compute_node.Item_getCurrentSiteValue()
source_project = compute_node.Item_getCurrentProjectValue()
source_section = compute_node.Item_getCurrentOwnerValue()
resource_value = compute_node.Item_getResourceValue()

if destination_project is None and source_project is not None:
  destination_project = source_project.getRelativeUrl()

if destination_section is None:
  destination_section = compute_node.getSourceAdministration()

if destination is None and source is not None:
  # We do not change location of the machine
  destination = source.getRelativeUrl()

if source is None and destination is None:
  raise ValueError("Sorry, destination is required for the initial set.")

if source_section is None:
  source_section = compute_node.getSourceAdministration()

resource_value = portal.product_module.compute_node

module = portal.getDefaultModule(portal_type=movement_portal_type)
line_portal_type = '%s Line' % movement_portal_type

delivery = module.newContent(title="Transfer %s to %s" % (compute_node.getTitle(), destination),
                             source_value=source,
                             source_section_value=source_section,
                             source_project_value=source_project,
                             destination=destination,
                             destination_section=destination_section,
                             source_decision=destination_section,
                             destination_decision=destination_section,
                             destination_project_value=destination_project,
                             start_date=DateTime(),
                             stop_date=DateTime(),
                             portal_type=movement_portal_type)

delivery_line = delivery.newContent(
                    portal_type=line_portal_type,
                    title=compute_node.getReference(),
                    quantity_unit=compute_node.getQuantityUnit(),
                    resource_value=resource_value)

delivery_line.edit(
              price=0.0,
              quantity=1.0,
              aggregate_value=compute_node)

delivery.confirm()
delivery.stop()
delivery.deliver()

delivery.reindexObject(activate_kw=dict(tag=tag))
delivery_line.reindexObject(activate_kw=dict(tag=tag))
