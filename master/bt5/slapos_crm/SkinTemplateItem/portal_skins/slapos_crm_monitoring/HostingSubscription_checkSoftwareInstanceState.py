from DateTime import DateTime
from erp5.component.module.DateUtils import addToDate

hosting_subscription = context
portal = context.getPortalObject()

if hosting_subscription.getMonitorScope() == "disabled":
  # Don't generate ticket if Monitor Scope is marked to disable
  return

if portal.ERP5Site_isSupportRequestCreationClosed():
  # Stop ticket creation
  return

date_check_limit = addToDate(DateTime(), to_add={'hour': -1})

if (date_check_limit - hosting_subscription.getCreationDate()) < 0:
  # Too early to check
  return

software_instance_list = context.portal_catalog(
  portal_type=["Software Instance", "Slave Instance"],
  specialise_uid=hosting_subscription.getUid(),
  **{"slapos_item.slap_state": ["start_requested"]})

has_newest_allocated_instance = False
has_unallocated_instance = False
failing_instance = None

# Check if at least one software Instance is Allocated
for instance in software_instance_list:
  if (date_check_limit - instance.getCreationDate()) < 0:
    continue

  if instance.getSlapState() != "start_requested":
    continue

  computer_partition = instance.getAggregateValue()
  if computer_partition is not None:
    has_newest_allocated_instance = True
    if instance.getPortalType() == "Software Instance" and \
        computer_partition.getParentValue().getMonitorScope() == "enabled" and \
        instance.SoftwareInstance_hasReportedError(tolerance=30):
      return context.HostingSubscription_createSupportRequestEvent(
        instance, 'slapos-crm-hosting-subscription-instance-state.notification')
  else:
    has_unallocated_instance = True
    failing_instance = instance

  if has_unallocated_instance and has_newest_allocated_instance:
    return context.HostingSubscription_createSupportRequestEvent(
      failing_instance, 'slapos-crm-hosting-subscription-instance-allocation.notification')

return
