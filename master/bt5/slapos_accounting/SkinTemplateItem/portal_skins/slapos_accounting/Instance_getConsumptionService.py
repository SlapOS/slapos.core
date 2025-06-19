portal = context.getPortalObject()
portal_type=context.getPortalType()
# Do simple now, need to define properly which service used
if portal_type == 'Software Instance':
  service = portal.service_module.software_instance_consumption
elif portal_type == 'Slave Instance':
  service = portal.service_module.slave_instance_consumption
else:
  raise ValueError('unknown instance type: %s' % portal_type)

return service, []
