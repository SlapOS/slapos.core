software_instance = context.JSONRPCService_getObjectFromData(data_dict)

# software_instance = context.getParentValue()
return {
  #"$schema": json_form.absolute_url().strip() + "/getOutputJSONSchema",
  "reference": software_instance.getReference(),
  "key": software_instance.getSslKey(),
  "certificate": software_instance.getSslCertificate(),
  "portal_type": "Software Instance Certificate Record",
}
