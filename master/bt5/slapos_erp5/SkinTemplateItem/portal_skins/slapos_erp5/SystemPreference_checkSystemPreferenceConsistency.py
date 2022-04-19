"""
  Verify the consistency of the System Preference for the SlapOS Master to
  ensure the site configuration is set.
"""

if context.getPortalType() not in ["System Preference"]:
  return []

error_list = []

if context.getId() == "slapos_default_system_preference" and context.getPreferenceState() != "global":
  error_list.append(
    "The Default System preference globally enabled shouldn't be slapos_default_system_preference" % context.getId())
  if fixit:
    context.globalEnable(comment="Enabled by PreferenceTool_checkSystemPreferenceConsistency")

if context.getPreferenceState() != "global":
  return []

if context.getId() != "slapos_default_system_preference":
  error_list.append(
    "The Default System preference globally enabled shouldn't be %s but slapos_default_system_preference" % context.getId())
  if fixit:
    context.disable(comment="Disabled by PreferenceTool_checkSystemPreferenceConsistency")


preference_method_list = [
  "getPreferredHateoasUrl",
  "getPreferredPayzenPaymentServiceReference",
  "getPreferredPayzenIntegrationSite",
  "getPreferredWechatPaymentServiceReference",
  "getPreferredWechatIntegrationSite"
  ]

for method_id in preference_method_list:
  result =  getattr(context.portal_preferences, method_id)()
  if result in [None, ""]:
    error_list.append(
      'The System Preference %s() should not return None or ""' % (method_id))

return error_list
