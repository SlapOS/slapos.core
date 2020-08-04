computer_list = []
for si in context.portal_catalog(url_string=context.getUrlString(),
                                 portal_type='Software Installation',
                                 validation_state='validated'):
  computer = si.getAggregateValue()
  if si.getSlapState() == 'start_requested' and \
      not computer.Computer_getSoftwareReleaseUsage(context.getUrlString()) \
      and computer.getValidationState() == 'validated':
    computer_list.append(computer)

return computer_list
