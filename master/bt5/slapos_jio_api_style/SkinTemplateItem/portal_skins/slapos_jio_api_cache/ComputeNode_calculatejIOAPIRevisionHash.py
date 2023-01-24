if context.getValidationState() != "validated":
  return None
import json
import hashlib
data = json.loads(context.asJSONText())
key_list = ["compute_node_id", "title", "compute_partition_list"]
hash_dict = {}
for key in key_list:
  hash_dict[key] = data.get(key, None)
return hashlib.md5(json.dumps(hash_dict, sort_keys=True)).hexdigest()
