software_release = context.portal_catalog.getResultValue(
  url_string={'query': context.getUrlString(), 'key': 'ExactMatch'},
  portal_type='Software Release')

if software_release is None:
  return ""

return "%s (%s)" % (software_release.getTitle(), software_release.getVersion())
