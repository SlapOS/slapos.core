portal = context.getPortalObject()
Base_getSlapOSattr = portal.Base_getSlapOSattr

security_uid_dict = Base_getSlapOSattr(portal, portal.portal_catalog.getSQLCatalog(), 'security_uid_dict')
delitem = Base_getSlapOSattr(portal, security_uid_dict, '__delitem__')

reverse_group_security_uid_dict = {}
reverse_groupless_security_uid_dict =  {}

for (group, role_set), security_uid in dict(security_uid_dict).iteritems():
  reverse_groupless_security_uid_dict[security_uid] = (group, role_set)
  try:
    reverse_security_uid_dict = reverse_group_security_uid_dict[group]
  except KeyError:
    reverse_security_uid_dict = reverse_group_security_uid_dict[group] = {}
  else:
    assert security_uid not in reverse_security_uid_dict
  reverse_security_uid_dict[security_uid] = role_set

# XXX: add support for aritrary groups
used_group_security_uid_dict = {
  '': {
    x.security_uid
    for x in portal.z_get_used_security_uid_list()
  },
  'computer' : {
    x.computer_security_uid
    for x in portal.z_get_used_computer_security_uid_list()
  },
  'project': {
    x.project_security_uid
    for x in portal.z_get_used_project_security_uid_list()
  },
  'user' : {
    x.user_security_uid
    for x in portal.z_get_used_user_security_uid_list()
  },
  'group': {
    x.group_security_uid
      for x in portal.z_get_used_group_security_uid_list()
  },
  'shadow': {
    x.shadow_security_uid
      for x in portal.z_get_used_shadow_security_uid_list()
  }
}

# Check unused security uid
for group, reverse_security_uid_dict in reverse_group_security_uid_dict.iteritems():
  used_security_uid_set = used_group_security_uid_dict[group]
  unused_security_uid_set = set(reverse_security_uid_dict).difference(used_security_uid_set)
  if unused_security_uid_set:
    print '# Will delete', len(unused_security_uid_set), 'security_uids in group', repr(group)
    for unused_security_uid in unused_security_uid_set:
      print '   * ', unused_security_uid, reverse_security_uid_dict[unused_security_uid]
      delitem((group, reverse_security_uid_dict[unused_security_uid]))
      portal.z_delete_security_uid_set_from_roles_and_users(uid=unused_security_uid)

# Check not deleted security uid in the roles_and_user_table
cataloged_security_uid_set = set([x.uid for x in portal.z_get_uid_group_from_roles_and_users()])
existing_security_uid_set = set(dict(security_uid_dict).values())

print '# Catalog secuirity_uid count', len(cataloged_security_uid_set)
print '# ZODB secuirity_uid count', len(existing_security_uid_set)

not_existing_security_uid_set = existing_security_uid_set.difference(cataloged_security_uid_set)
print '# Not catalogued', len(not_existing_security_uid_set), 'security_uid'
for security_uid in not_existing_security_uid_set:
  print '   * ', security_uid, reverse_groupless_security_uid_dict[security_uid]

not_existing_security_uid_set = cataloged_security_uid_set.difference(existing_security_uid_set)
if not_existing_security_uid_set:

  print '# Will uncatalog', len(not_existing_security_uid_set), 'security_uid'
  print '    * like: ', list(not_existing_security_uid_set)[:10]
  for security_uid in not_existing_security_uid_set:
    assert security_uid not in reverse_groupless_security_uid_dict
    portal.z_delete_security_uid_set_from_roles_and_users(security_uid=security_uid)

if 0:
  print 'DRY'
  context.REQUEST.RESPONSE.write(printed)
  raise Exception('dry')
return printed
