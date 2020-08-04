portal = context.getPortalObject()

content_dict = {}
for test_component in portal.portal_components.searchFolder(portal_type='Test Component'):
  if "Slap" not in test_component.getId():
    continue
  content_dict[test_component.getId()] = test_component.getTextContent()

print len(content_dict)

for skin_folder in portal.portal_skins.objectValues('Folder'):
  if not skin_folder.getId().startswith("slapos"):
    continue
  for skin in skin_folder.objectValues():
    if skin.getId().startswith("Alarm_"):
      continue

    if skin.meta_type in ('Script (Python)', 'Z SQL Method', ):
      found = 0
      for _, content in content_dict.iteritems():
        if skin.getId() in content:
          found = 1
          break
      if not found:
        print "%s/%s" % (skin_folder.getId(), skin.getId())
  
container.REQUEST.RESPONSE.setHeader('content-type', 'text/plain')
return '\n'.join(sorted(printed.splitlines()))
