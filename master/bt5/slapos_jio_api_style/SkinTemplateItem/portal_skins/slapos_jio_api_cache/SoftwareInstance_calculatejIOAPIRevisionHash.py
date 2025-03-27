if context.getValidationState() != "validated" or context.getSlapState() == "draft":
  return None
import json
import hashlib
data = json.loads(context.asJSONText())
key_list = ["software_release_uri", "software_type", "state", "connection_parameters", "parameters"]
hash_dict = {}
for key in key_list:
  hash_dict[key] = data.get(key, None)
return hashlib.md5(json.dumps(hash_dict, sort_keys=True)).hexdigest()
