"""
Check if this instance tree is upgradable to the latest version,
and return the software release to upgrade with.
"""

instance_tree = context
portal = context.getPortalObject()

slap_state = ['start_requested', 'stop_requested']

if not instance_tree.getSlapState() in slap_state:
  return None

source_instance_list = [q for q in instance_tree.getSuccessorValueList() if q.getSlapState() in slap_state]
if len(source_instance_list) == 0:
  return None
source_instance = source_instance_list[0]

software_release = instance_tree.InstanceTree_getNewerSofwareRelease()
if not software_release:
  return None

computer = source_instance.getAggregateValue().getParentValue()
if computer.getValidationState() != 'validated':
  return None
      
#Find Software Installation
software_installation_list = portal.portal_catalog(
    portal_type="Software Installation",
    validation_state="validated",
    url_string=software_release.getUrlString(),
    default_aggregate_uid=computer.getUid(),
  )
# check again slap_state because it might be ignored in previous request!
if 'start_requested' in [software_installation.getSlapState() \
             for software_installation in software_installation_list]:
  return software_release

return None
