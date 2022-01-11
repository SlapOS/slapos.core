from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

if context.getPortalType() not in ('Software Instance', 'Slave Instance'):
  raise TypeError('%s is not supported' % context.getPortalType())

software_instance = context
if (software_instance.getValidationState() == 'validated') \
  and (software_instance.getSlapState() == 'destroy_requested'):

  partition = software_instance.getAggregateValue(portal_type='Compute Partition')

  if partition is None:
    software_instance.invalidate(comment='Invalidated as unallocated and destroyed')

  elif (partition.getParentValue().getPortalType() == 'Compute Node') and \
    (software_instance.getPortalType() == 'Slave Instance'):
    # Invalidate ONLY IF the partition is inside a Compute Node, which does not report destruction
    software_instance.invalidate(comment='Invalidated as Compute Node does not report destruction of Slave Instance')

  # Software Instance allocated on a Compute Node is invalidated by SlapTool
