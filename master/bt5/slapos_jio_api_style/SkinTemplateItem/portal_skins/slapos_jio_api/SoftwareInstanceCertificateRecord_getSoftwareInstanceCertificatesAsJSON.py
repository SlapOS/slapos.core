import json
software_instance = context.getParentValue()
return json.dumps({
  "$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "reference": software_instance.getReference(),
  "key": software_instance.getSslKey(),
  "certificate": software_instance.getSslCertificate(),
  "portal_type": "Software Instance Certificate Record",
}, indent=2)
