"""
  Create an internal Packing List and attach the computer
"""
from DateTime import DateTime
from zExceptions import Unauthorized

user = context.getPortalObject().portal_membership.getAuthenticatedMember().getUserValue()

if user is None or user.getRelativeUrl() != context.getDestinationSection():
  raise Unauthorized("Only the Instance Tree owner can transfer it from one location to another.")

portal_type = "Internal Packing List"

source = context.Item_getCurrentSiteValue()
source_project = context.Item_getCurrentProjectValue()
source_section = context.Item_getCurrentOwnerValue()
resource_value = context.Item_getResourceValue()

if destination_project is None and source_project is not None:
  destination_project = source_project.getRelativeUrl()

destination_section = context.getDestinationSection()

if source_section is None:
  source_section = context.getDestinationSectionValue()

if destination is None and source is not None:
  destination = source.getRelativeUrl() 

resource_value = context.product_module.computer

module = context.getDefaultModule(portal_type=portal_type)
line_portal_type = '%s Line' % portal_type

delivery = module.newContent(title="Transfer %s to %s" % (context.getTitle(), destination_project),
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
                             portal_type=portal_type)

delivery_line = delivery.newContent(
                    portal_type=line_portal_type,
                    title=context.getReference(),
                    quantity_unit=context.getQuantityUnit(),
                    resource_value=resource_value)

delivery_line.edit(
              price=0.0,
              quantity=1.0,
              aggregate_value=context)


delivery.confirm()
delivery.stop()
delivery.deliver()
