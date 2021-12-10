requester_instance = state_change['object']
portal = requester_instance.getPortalObject()
from zExceptions import Unauthorized
from DateTime import DateTime

assert requester_instance.getPortalType() == 'Instance Tree'

# Get required arguments
kwargs = state_change.kwargs

# Required args
# Raise TypeError if all parameters are not provided
try:
  # destination=None, destination_project=None
  destination = kwargs['destination']
  destination_project = kwargs["destination_project"]
except KeyError:
  raise TypeError("InstanceTree_requestTransfer takes exactly 2 arguments")

user = portal.portal_membership.getAuthenticatedMember().getUserValue()
if user is None or user.getRelativeUrl() != requester_instance.getDestinationSection():
  raise Unauthorized("Only the Instance Tree owner can transfer it from one location to another.")

tag = "%s_%s_%s_inProgress" % (requester_instance.getUid(), destination, destination_project)

if (portal.portal_activities.countMessageWithTag(tag) > 0):
  # The software instance is already under creation but can not be fetched from catalog
  # As it is not possible to fetch informations, it is better to raise an error
  raise NotImplementedError(tag)

movement_portal_type = "Internal Packing List"

source = requester_instance.Item_getCurrentSiteValue()
source_project = requester_instance.Item_getCurrentProjectValue()
source_section = requester_instance.Item_getCurrentOwnerValue()
resource_value = requester_instance.Item_getResourceValue()

if destination_project is None and source_project is not None:
  destination_project = source_project.getRelativeUrl()

destination_section = requester_instance.getDestinationSection()

if source_section is None:
  source_section = requester_instance.getDestinationSectionValue()

if destination is None and source is not None:
  destination = source.getRelativeUrl() 

resource_value = requester_instance.product_module.compute_node


module = portal.getDefaultModule(portal_type=movement_portal_type)
line_portal_type = '%s Line' % movement_portal_type

delivery = module.newContent(title="Transfer %s to %s" % (requester_instance.getTitle(), destination_project),
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
                    title=requester_instance.getReference(),
                    quantity_unit=requester_instance.getQuantityUnit(),
                    resource_value=resource_value)

delivery_line.edit(
              price=0.0,
              quantity=1.0,
              aggregate_value=requester_instance)


delivery.confirm()
delivery.stop()
delivery.deliver()

delivery.reindexObject(activate_kw=dict(tag=tag))
delivery_line.reindexObject(activate_kw=dict(tag=tag))
