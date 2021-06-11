instance_tree = context

software_instance = instance_tree.getSuccessorValue()
if not software_instance:
  return None
software_release_list = context.SoftwareProduct_getSortedSoftwareReleaseList(
                          software_release_url=software_instance.getUrlString())

if not software_release_list:
  return None
latest_software_release = software_release_list[0]
if latest_software_release.getUrlString() == software_instance.getUrlString():
  return None
else:
  return latest_software_release
