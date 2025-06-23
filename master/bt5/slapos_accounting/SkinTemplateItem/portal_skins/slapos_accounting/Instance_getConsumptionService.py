portal = context.getPortalObject()
portal_type=context.getPortalType()
# Do simple now
if portal_type in ('Software Instance', 'Slave Instance'):
  service = portal.service_module.instance_consumption
else:
  raise ValueError('unknown instance type: %s' % portal_type)

return service
