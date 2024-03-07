group_by_list = ["url_string", "source_reference", "follow_up_title"]
sql_result_list = context.getPortalObject().portal_catalog(
  select_list=group_by_list+['count(*)'],
  portal_type="Instance Tree",
  title="_remote_%",
  #url_string="https://lab.nexedi.com/nexedi/slapos/%",
  slap_state=["start_requested", "stop_requested"],
  group_by=group_by_list,
  #sort_on=[['count(*)', 'DESC']]
)

soft_proj_dict = {}

for sql_result in sql_result_list:
  soft = sql_result['url_string'].split('/')[-2] + ' <i>' + sql_result['source_reference'] + '</i>'
  project = sql_result['follow_up_title']

  """
  if project not in project_soft_dict:
    project_soft_dict[project] = {}
  if soft not in project_soft_dict[project]:
    project_soft_dict[project][soft] = 0
  project_soft_dict[project][soft] = project_soft_dict[project][soft] + int(sql_result['count(*)'])
  """
  if soft not in soft_proj_dict:
    soft_proj_dict[soft] = {'project_list': [], 'count': 0}
  soft_proj_dict[soft]['project_list'].append(project)
  soft_proj_dict[soft]['count'] = soft_proj_dict[soft]['count'] + int(sql_result['count(*)'])

print('<ul>')
"""
for project, soft_dict in project_soft_dict.items():
  print '<li><p>%s</p><ul>' % project
  for soft, count in soft_dict.items():
    print '<li><p>%s <b>%i</b></p></li>' % (soft, count)
  print '</ul></li>'
"""
ordered_list = soft_proj_dict.items()
ordered_list.sort()
for soft, info_dict in ordered_list:
  print('<li><p>%s <b>%i</b> %s</p>' % (soft, info_dict['count'], str(list(set(info_dict['project_list'])))))
  """
  for proj in list(set(info_dict['project_list'])):
    print '<li><p>%s</p></li>' % (proj)
  """
  print('</li>')
print('</ul>')

context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/html')
return printed
