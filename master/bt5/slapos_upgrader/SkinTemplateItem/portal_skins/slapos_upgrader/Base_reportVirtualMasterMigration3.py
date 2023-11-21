portal = context.getPortalObject()

instance_tree_dict = {}

for sql_result in portal.portal_catalog(title='slapmigration',
                                        portal_type='Compute Partition'):
  partition = sql_result.getObject()
  assert partition.getParentValue().getPortalType() == 'Remote Node'

  instance = partition.getAggregateRelatedValue(portal_type='Software Instance')
  if partition.getSlapState() == 'free':
    assert instance is None
    continue

  assert partition.getSlapState() == 'busy'
  assert instance is not None
  assert instance.getSlapState() != 'destroy_requested'
  assert instance.getValidationState() == 'validated'

  instance_tree = instance.getSpecialiseValue()
  if (instance_tree.getTitle() == instance.getTitle()):
    # disconnected trees...
    #assert len(instance_tree.getSpecialiseRelatedValueList()) == 1, instance_tree.getRelativeUrl()
    continue

  instance_tree_dict[instance_tree.getRelativeUrl()] = instance_tree

print('<h1>Broken instances (allocated on multiple virtual master)</h1>')
print('<ol>')

print_info_list = []
for instance_tree_relative_url, instance_tree in instance_tree_dict.items():
  title = instance_tree.getTitle()
  relative_url = instance_tree_relative_url
  if title.startswith('_remote_'):
    original_instance_reference = title.split('_')[3]
    original_instance = portal.portal_catalog.getResultValue(reference=original_instance_reference, portal_type='Software Instance')
    title = original_instance.getSpecialiseTitle()
    relative_url = original_instance.getSpecialise()

  broken_instance_list = []
  for software_instance in portal.portal_catalog(
    specialise__uid=instance_tree.getUid(),
    portal_type='Software Instance',
    aggregate__title='slapmigration'
  ):
    broken_instance_list.append((
      software_instance.getAggregateValue().getParentValue().getDestinationProjectTitle(),
      software_instance.getRelativeUrl(),
      software_instance.getTitle()
    ))
  broken_instance_list.sort()
  print_info_list.append((instance_tree.getFollowUpTitle(), relative_url, title, instance_tree.getDestinationSectionTitle(), broken_instance_list))

sorted(print_info_list, key=lambda print_info: print_info[0])
print_info_list.sort()
for print_info in print_info_list:
  print('<li><p><b>%s</b> <a href="%s">%s</a> (%s) </p><ul>' % print_info[:-1])
  for instance_info in print_info[-1]:
    print('<li><i>%s</i> <a href="%s">%s</a></li>' % instance_info)
  print('</ul></li>')
print('</ol>')

context.REQUEST.RESPONSE.setHeader('Content-Type', 'text/html')
return printed
