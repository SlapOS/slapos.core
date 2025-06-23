error_log = []

if context.getPortalType() not in ["System Preference"]:
  return []

if context.getId() == "slapos_default_system_preference" and context.getPreferenceState() != "global":
  error_log.extend(context.SystemPreference_checkSystemPreferenceConsistency(fixit=fixit, **kw))

if context.getPreferenceState() != "global":
  return []

url = context.getPreferredDocumentConversionServerUrlList()

if not url:
  fixing = ''
  if fixit:
    # Set some value if no value is set.
    context.setPreferredDocumentConversionServerUrlList(['https://cloudooo1.erp5.net/', 'https://cloudooo.erp5.net/'])
    fixing = ' (fixed, set https://cloudooo1.erp5.net/ and https://cloudooo.erp5.net/)'

  error_log.append("Conversion Server is not configured. %s" % fixing)

return error_log
