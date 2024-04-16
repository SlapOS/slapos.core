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

return False
