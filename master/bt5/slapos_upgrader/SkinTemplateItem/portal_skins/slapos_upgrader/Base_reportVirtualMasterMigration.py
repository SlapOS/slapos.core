# https://playground.diagram.codes/d/graph

print "ARROWS"
print ""

project_dict = {}
remote_project_dict = {}

group_by_list = ["follow_up__uid"]
sql_result_list = context.getPortalObject().portal_catalog(
  select_list=group_by_list+['count(*)'],
  portal_type="Instance Tree",
  slap_state=["start_requested", "stop_requested"],
  group_by=group_by_list
)
for sql_result in sql_result_list:
  project_dict[sql_result.getFollowUpUid()] = {
    'title': '%s (%s)' % (sql_result.getFollowUpTitle(), sql_result['count(*)']),
    'remote_uid_list': []
  }

  for sql_remote in context.getPortalObject().portal_catalog(
    portal_type="Remote Node",
    follow_up__uid=sql_result.getFollowUpUid()
  ):
    project_dict[sql_result.getFollowUpUid()]['remote_uid_list'].append(sql_remote.getDestinationProjectUid())
    remote_project_dict[sql_remote.getDestinationProjectUid()] = True

  project_dict[sql_result.getFollowUpUid()]['remote_uid_list'] = sorted(project_dict[sql_result.getFollowUpUid()]['remote_uid_list'])

# Calculate all the nodes
# Remote projects will be standalone
# Other project will be grouped by their remote
display_dict = {}
for project_uid, project_value_dict in project_dict.items():
  if project_uid in remote_project_dict:
    display_dict[project_uid] = project_value_dict
  else:
    remote_key = 'remote_%s' % ''.join(sorted([str(x) for x in project_value_dict['remote_uid_list']])) or 'couscous'
    if remote_key not in display_dict:
      display_dict[remote_key] = {
        'remote_uid_list': project_value_dict['remote_uid_list'],
        'title': project_value_dict['title']
      }
    else:
      display_dict[remote_key]['title'] = '%s\n%s' % (display_dict[remote_key]['title'], project_value_dict['title'])

for display_key, display_value in display_dict.items():
  print '"%s" as %s' % (display_value['title'], display_key)
print ''

for display_key, display_value in display_dict.items():
  has_remote = False
  for remote_uid in display_value['remote_uid_list']:
    if remote_uid in display_dict:
      # only not destroyed links
      has_remote = True
      print '%s->%s' % (display_key, remote_uid)
  if (not has_remote) and (display_key not in remote_project_dict):
    print '%s->%s' % (display_key, display_key)
print ''


return printed
