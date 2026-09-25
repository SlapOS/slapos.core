from Products.CMFActivity.ActiveResult import ActiveResult

portal = context.getPortalObject()
active_process = context.newActiveProcess()

for security_uid_column in ["computer_security_uid", "function_security_uid",
                            "group_security_uid", "project_security_uid",
                            "security_uid", "shadow_security_uid",
                            "subscription_security_uid", "user_security_uid"]:

  missing_security_uid_list = portal.z_search_unindexed_security_uid(
    security_uid_column=security_uid_column)

  if len(missing_security_uid_list) > 0:
    summary = "Security UIDs are inconsistent"
    if fixit:
      summary += " (fixing it)"
      portal.z_refresh_roles_and_users()

    active_process.postResult(ActiveResult(
         summary=summary,
         severity=100,
         detail="Missing Security Uid List on %s : %s " % (security_uid_column,
           [i.security_uid for i in missing_security_uid_list])))
    return
