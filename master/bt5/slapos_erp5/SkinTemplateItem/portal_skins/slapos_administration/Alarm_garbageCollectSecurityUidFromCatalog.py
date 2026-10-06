from Products.CMFActivity.ActiveResult import ActiveResult

portal = context.getPortalObject()
active_process = context.newActiveProcess()

reverse_group_security_uid_dict = {}
reverse_groupless_security_uid_dict =  {}

local_group_id_list = [i for i in portal.portal_categories.local_role_group.objectIds()]
security_uid_column_list = ['%s_security_uid' % g for g in local_group_id_list]

local_group_id_list += ['']
security_uid_column_list += ['security_uid']

for security_uid_column in security_uid_column_list:
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
    # Break loop earlier, since it is not wise to configure
    return active_process

used_group_security_uid_dict = {
  group: {
    x.used_security_uid for x in portal.z_get_used_security_uid_list(column_type=group)
  } for group in local_group_id_list
}

for group, role, security_uid in portal.ERP5Site_getSecurityUidListForRecreateTable():
  reverse_security_uid_dict = reverse_group_security_uid_dict.setdefault(group, {})
  role_set = reverse_security_uid_dict.setdefault(security_uid, [])
  role_set.append(role)
  previous = reverse_groupless_security_uid_dict.get(security_uid)
  if previous is None:
    reverse_groupless_security_uid_dict[security_uid] = (group, role_set)
  else:
    assert previous[0] == group

# Check unused security uid
for group, reverse_security_uid_dict in reverse_group_security_uid_dict.items():
  unused_security_uid_set = set(reverse_security_uid_dict).difference(
    used_group_security_uid_dict[group])

  if unused_security_uid_set:
    summary = 'Found UIDs to delete from %s' % (group)
    detail = 'Found UIDs to delete %s security_uids in group %s' % (len(unused_security_uid_set), group)
    if fixit:
      summary += " (fixing it)"
      for unused_security_uid in unused_security_uid_set:
        detail += '(%s %s),' % (unused_security_uid, reverse_security_uid_dict[unused_security_uid])
        portal.ERP5Site_deleteSecurityUidDictEntry(
          sql_catalog=portal.portal_catalog.getSQLCatalog(),
          entry=(group, tuple(reverse_security_uid_dict[unused_security_uid])))
        portal.z_delete_security_uid_set_from_roles_and_users(uid=unused_security_uid)

    active_process.postResult(ActiveResult(
         summary=summary, severity=100, detail=detail))

# Check not deleted security uid in the roles_and_user_table
cataloged_security_uid_set = set([x.uid for x in portal.z_get_uid_group_from_roles_and_users()])
existing_security_uid_set = set(
  security_uid for group, role, security_uid in context.ERP5Site_getSecurityUidListForRecreateTable())

not_existing_security_uid_set = existing_security_uid_set.difference(cataloged_security_uid_set)
if len(not_existing_security_uid_set):
  summary = "Found UIDs missing in catalog (zodb) %s security_uids" % len(not_existing_security_uid_set)
  detail = " ("
  for security_uid in not_existing_security_uid_set:
    detail += '(%s %s),' % (security_uid, reverse_groupless_security_uid_dict[security_uid])
  detail += ")"
  active_process.postResult(ActiveResult(
    summary=summary, severity=100, detail=detail))

not_existing_security_uid_set = cataloged_security_uid_set.difference(existing_security_uid_set)
if not_existing_security_uid_set:
  summary = "Found UIDs removed from in catalog (mariadb) %s security_uids" % len(not_existing_security_uid_set)
  detail = "Sample: "
  for security_uid in list(not_existing_security_uid_set)[:10]:
    detail += '(%s %s),' % (security_uid, reverse_groupless_security_uid_dict.get(security_uid))
  if fixit:
    for security_uid in not_existing_security_uid_set:
      assert security_uid not in reverse_groupless_security_uid_dict
      portal.z_delete_security_uid_set_from_roles_and_users(uid=security_uid)
  active_process.postResult(ActiveResult(
    summary=summary, severity=100, detail=detail))

return active_process
