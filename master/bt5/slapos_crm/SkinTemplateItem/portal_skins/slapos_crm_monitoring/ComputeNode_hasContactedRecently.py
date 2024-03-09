portal = context.getPortalObject()
compute_node = context
now_date = DateTime()

if (now_date - compute_node.getCreationDate()) < maximum_days:
  # This compute_node was created recently skip
  return True

message_dict = context.getAccessStatus()
# Ignore if data isn't present.
if message_dict.get("no_data", None) == 1:
  message_dict = {}

if 'created_at' in message_dict:
  contact_date = DateTime(message_dict.get('created_at').encode('utf-8'))
  return (now_date - contact_date) < maximum_days

# If no access status information, check in consumption report
for sale_packing_list in portal.portal_catalog(
         portal_type="Sale Packing List Line",
         simulation_state="delivered",
         default_aggregate_uid=compute_node.getUid(),
         sort_on=[('movement.start_date', 'DESC')],
         limit=1):
  return (now_date - sale_packing_list.getStartDate()) < maximum_days

return False
