error_log = []

if context.getPortalType() not in ["System Preference"]:
  return []

if context.getId() == "slapos_default_system_preference" and context.getPreferenceState() != "global":
  error_log.extend(context.SystemPreference_checkSystemPreferenceConsistency(fixit=fixit, **kw))

if context.getPreferenceState() != "global":
  return []

portal = context.getPortalObject()
system_preference = context
expected_url = portal.ERP5Site_getConfigurationCloudoooUrl()
url = system_preference.getPreferredDocumentConversionServerUrl()

if expected_url != url:
  fixing = ''
  if fixit:
    system_preference.setPreferredDocumentConversionServerUrl(expected_url)
    fixing = ' (fixed)'
  
  error_log.append("Conversion Server not configured as expected%s: %s" %
    (fixing, "Expect %s\nGot %s" % (expected_url, url)))

return error_log
