causality_portal_type_list = [
  'Compute Node',
  'Instance Tree'
]

if (context.getSimulationState() == "invalidated") or \
    (context.getPortalType() != "Support Request") or \
    (not context.getCausality(portal_type=causality_portal_type_list)):
  # Nothing to check
  return


document = context.getCausalityValue(portal_type=causality_portal_type_list)
causality_portal_type = document.getPortalType()
if causality_portal_type == "Compute Node":
  error_dict = document.ComputeNode_getReportedErrorDict()
  return error_dict['message']

if causality_portal_type == "Instance Tree":
  message_list = []
  instance_tree = document

  software_instance_list = instance_tree.getSpecialiseRelatedValueList(
                 portal_type=["Software Instance", "Slave Instance"])

  # Check if at least one software Instance is Allocated
  for instance in software_instance_list:
    error_dict = instance.SoftwareInstance_getReportedErrorDict(tolerance=30)
    if error_dict['should_notify']:
      message_list.append(error_dict['message'])
  return ",".join(message_list)
return None
