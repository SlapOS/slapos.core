from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

from erp5.component.module.DateUtils import getClosestDate

instance_tree = context
portal = context.getPortalObject()

workflow_item_list = portal.portal_workflow.getInfoFor(
  ob=instance_tree,
  name='history',
  wf_id='instance_slap_interface_workflow')
start_date = None
for item in workflow_item_list:
  start_date = item.get('time')
  if start_date:
    break

if start_date is None:
  # Compatibility with old Instance tree
  start_date = instance_tree.getCreationDate()

start_date = getClosestDate(target_date=start_date, precision='day')

return start_date