# Do need to generate invoices in case no section are defined
source_section = context.getSourceSection()
destination_section = context.getDestinationSection()
if source_section == destination_section or source_section is None \
    or destination_section is None:
  return None

# Do not expand if packing list is not consistent
if context.checkConsistency():
  return None

return 'default_delivery_rule'
