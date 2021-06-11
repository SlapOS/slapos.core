request = context.REQUEST
edit_kw = {}

if monitor_scope is not None and monitor_scope != context.getMonitorScope():
  edit_kw["monitor_scope"] = monitor_scope

if upgrade_scope is not None and upgrade_scope != context.getUpgradeScope():
  edit_kw["upgrade_scope"] = upgrade_scope

if short_title != context.getShortTitle():
  edit_kw["short_title"] = short_title

if description != context.getDescription():
  edit_kw["description"] = description

if edit_kw.keys():
  context.edit(**edit_kw)

def isSoftwareTypeChanged(software_type):
  base_type = ['RootSoftwareInstance', 'default']
  current_software_type = context.getSourceReference()
  if software_type in base_type and current_software_type in base_type:
    return False
  else:
    return current_software_type != software_type

if 'software_type' in request and isSoftwareTypeChanged(request['software_type']):
  raise ValueError("Change Software Type is forbidden.")

if context.getTextContent() != text_content:
  context.InstanceTree_requestPerson(instance_xml=text_content')
